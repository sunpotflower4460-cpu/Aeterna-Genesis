// Explicit local fuel/waste encounters and counted reservoir contacts.
// No body labels, permeability masks, protective functions or growth targets.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

template<class T> void binary(const std::filesystem::path &p,const std::vector<T>& x) {
  std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(x.data()),x.size()*sizeof(T));
  if(!f)throw std::runtime_error("checkpoint write failed");
}

int main(int argc,char**argv) {
 try {
  if(argc==7&&std::string(argv[1])=="--rates"){
    double e=std::stod(argv[2]),f=std::stod(argv[3]),p=std::stod(argv[4]),h=std::stod(argv[5]);int z=2*std::stoi(argv[6]);
    std::cout<<std::setprecision(17)<<"n,bp,ip,bd_pair,id_pair\n";
    for(int n=0;n<=z;++n)std::cout<<n<<','<<p*std::exp(f+e*n)<<','<<p<<','<<h*std::exp(.5*e*n+f)/z<<','<<h*std::exp(-.5*e*n)/z<<'\n';
    return 0;
  }
  if(argc!=20)throw std::runtime_error("N d M T seed epsilon df passive eta DB DI DF DW kex source mu ztotal initialB out");
  const int N=std::stoi(argv[1]),d=std::stoi(argv[2]),M=std::stoi(argv[3]),z=2*d;
  const double T=std::stod(argv[4]);const uint64_t seed=std::stoull(argv[5]);
  const double eps=std::stod(argv[6]),df=std::stod(argv[7]),passive=std::stod(argv[8]),eta=std::stod(argv[9]);
  const std::array<double,5> D={0.,std::stod(argv[11]),std::stod(argv[10]),std::stod(argv[12]),std::stod(argv[13])};
  double kex=std::stod(argv[14]);const std::string source=argv[15];
  const double mu=std::stod(argv[16]),ztotal=std::stod(argv[17]),initialB=std::stod(argv[18]);
  const std::filesystem::path out=argv[19];
  int V=1;for(int a=0;a<d;++a)V*=N;
  const int samples=std::lround(T/10),B0=int(M*initialB);
  if(N<3||(d!=2&&d!=3)||M<1||M>=V||T<0||std::abs(T-10*samples)>1e-8||eps>0||passive<0||eta<0||kex<0||ztotal<=0||initialB<0||initialB>1||std::abs(mu)>50)
    throw std::runtime_error("invalid physical parameters");
  for(double x:D)if(x<0||!std::isfinite(x))throw std::runtime_error("invalid diffusivity");
  if(source=="closed")kex=0;
  else if(source=="uniform")kex/=N;
  else if(source!="plane")throw std::runtime_error("unknown reservoir geometry");
  if(std::filesystem::exists(out/"series.csv"))throw std::runtime_error("refuse existing history");
  const double zF=ztotal/(1+std::exp(-mu)),zW=ztotal/(1+std::exp(mu));
  const double logF=std::log(zF),logW=std::log(zW),exchange_bound=kex*std::max(1.,ztotal);
  const int contacts=source=="uniform"?V:V/N;
  const int fuel0=std::lround((V-M)*ztotal/(1+ztotal));
  const int F0=int(fuel0/(1+std::exp(-mu))),W0=fuel0-F0;
  std::array<double,7> bp{},ip{},bd{},id{},hop{};
  std::array<double,5> pbar{},dbar{},bound{};
  for(int n=0;n<=z;++n) {
    ip[n]=passive;bp[n]=passive*std::exp(df+eps*n);
    id[n]=eta*std::exp(-.5*eps*n);bd[n]=eta*std::exp(.5*eps*n+df);
    hop[n]=std::exp(eps*n);
    pbar[1]=std::max(pbar[1],ip[n]);pbar[2]=std::max(pbar[2],bp[n]);
    dbar[1]=std::max(dbar[1],id[n]);dbar[2]=std::max(dbar[2],bd[n]);
  }
  for(int s=1;s<=4;++s){bound[s]=D[s]+pbar[s]+dbar[s];if(!std::isfinite(bound[s]))throw std::runtime_error("nonfinite proposal bound");}
  std::vector<std::array<int,6>> neighbor(V);
  for(int x=0;x<V;++x){int jump=1;for(int a=0;a<d;++a){int c=(x/jump)%N;
    neighbor[x][2*a]=c+1==N?x-(N-1)*jump:x+jump;
    neighbor[x][2*a+1]=c==0?x+(N-1)*jump:x-jump;jump*=N;}}
  std::mt19937_64 initial_rng(seed^0x9e3779b97f4a7c15ULL),rng(seed^0xd1b54a32d192ed03ULL);
  auto index=[&](int k){return std::uniform_int_distribution<int>(0,k-1)(rng);};
  auto uniform=[&](){return ((rng()>>12)+.5)*0x1p-52;};
  std::vector<int32_t> permutation(V);std::iota(permutation.begin(),permutation.end(),0);
  for(int i=0;i<M+fuel0;++i){int j=std::uniform_int_distribution<int>(i,V-1)(initial_rng);std::swap(permutation[i],permutation[j]);}
  std::vector<uint8_t> cell(V,0),nb(V,0);
  std::vector<int32_t> macro_at(V,-1),position(permutation.begin(),permutation.begin()+M);
  std::vector<int64_t> displacement(M*d,0);
  for(int p=0;p<M;++p){cell[position[p]]=p<B0?2:1;macro_at[position[p]]=p;}
  for(int p=0;p<fuel0;++p)cell[permutation[M+p]]=p<F0?3:4;
  std::array<std::vector<int>,5> lists;std::vector<int> rank(V);
  for(int x=0;x<V;++x){rank[x]=lists[cell[x]].size();lists[cell[x]].push_back(x);for(int a=0;a<z;++a)nb[x]+=cell[neighbor[x][a]]==2;}
  auto set_type=[&](int x,int type){auto &from=lists[cell[x]];auto &to=lists[type];int last=from.back();from[rank[x]]=last;rank[last]=rank[x];from.pop_back();rank[x]=to.size();to.push_back(x);cell[x]=type;};
  int64_t NB=B0,pairs=0;
  for(int x=0;x<V;++x)if(cell[x]==2)pairs+=nb[x];pairs/=2;
  const long double H0=df*NB+eps*pairs;
  long double medium=0;
  uint64_t proposals=0,reservoir_proposals=0;
  std::array<int64_t,4> exchange{}; // Fin,Fout,Win,Wout
  std::array<int64_t,5> hops{};
  std::array<std::array<int64_t,7>,4> reactions{}; // passive BI/IB, driven BI/IB
  std::array<std::vector<int64_t>,5> xflow;
  std::array<std::vector<int64_t>,4> rxn_x,exchange_x;
  for(auto &a:xflow)a.resize(N,0);for(auto &a:rxn_x)a.resize(N,0);for(auto &a:exchange_x)a.resize(N,0);
  auto snapshot=[&](int sample){
    const auto prefix=out/("state-"+std::to_string(sample));
    std::vector<uint8_t> conformer(M);for(int p=0;p<M;++p)conformer[p]=cell[position[p]]-1;
    binary(prefix.string()+"-cells.bin",cell);binary(prefix.string()+"-positions.bin",position);
    binary(prefix.string()+"-conformers.bin",conformer);binary(prefix.string()+"-displacements.bin",displacement);
  };
  std::ofstream obs(out/"series.csv");obs<<std::setprecision(17);
  obs<<"time,molecules,B,I,F,W,vacancies,pairs,H,work,heat,heat_budget_error,proposals,reservoir_proposals,F_in,F_out,W_in,W_out,msd,fuel_mixing_information";
  for(int a=0;a<d;++a)obs<<",mean_dx"<<a;
  for(int s=1;s<=4;++s)obs<<",hops_"<<s;
  for(int s=0;s<4;++s)for(int n=0;n<=z;++n)obs<<",rxn_"<<s<<'_'<<n;
  for(int s=0;s<=4;++s)for(int x=0;x<N;++x)obs<<",profile_"<<s<<'_'<<x;
  for(int s=1;s<=4;++s)for(int x=0;x<N;++x)obs<<",xflow_"<<s<<'_'<<x;
  for(int s=0;s<4;++s)for(int x=0;x<N;++x)obs<<",rxnx_"<<s<<'_'<<x;
  for(int s=0;s<4;++s)for(int x=0;x<N;++x)obs<<",source_"<<s<<'_'<<x;
  obs<<'\n';
  auto measure=[&](int sample){
    std::array<int64_t,5> counts{};int64_t actual_pairs=0;
    std::array<std::vector<int64_t>,5> profile;for(auto &a:profile)a.resize(N,0);
    for(int x=0;x<V;++x){
      counts[cell[x]]++;profile[cell[x]][x%N]++;
      int n=0;for(int a=0;a<z;++a)n+=cell[neighbor[x][a]]==2;
      if(n!=nb[x])throw std::runtime_error("independent neighbor count failed");
      if(cell[x]==2)actual_pairs+=n;
      if(rank[x]<0||size_t(rank[x])>=lists[cell[x]].size()||lists[cell[x]][rank[x]]!=x)throw std::runtime_error("scheduler membership disagrees with physical state");
      if((cell[x]==1||cell[x]==2)!=(macro_at[x]>=0))throw std::runtime_error("macro identity attached to wrong species");
    }
    for(int s=0;s<=4;++s)if(counts[s]!=int64_t(lists[s].size()))throw std::runtime_error("scheduler species count failed");
    std::array<int64_t,4> rxn{};for(int s=0;s<4;++s)for(int n=0;n<=z;++n)rxn[s]+=reactions[s][n];
    if(counts[1]+counts[2]!=M||counts[2]!=NB||actual_pairs!=2*pairs||NB!=B0-rxn[0]+rxn[1]-rxn[2]+rxn[3]||
       counts[3]!=F0+exchange[0]-exchange[1]-rxn[2]+rxn[3]||counts[4]!=W0+exchange[2]-exchange[3]+rxn[2]-rxn[3])
      throw std::runtime_error("independent stoichiometric or pair count failed");
    for(int p=0;p<M;++p)if(macro_at[position[p]]!=p)throw std::runtime_error("macro identity lost");
    const long double H=df*NB+eps*pairs,work=logF*(exchange[0]-exchange[1])+logW*(exchange[2]-exchange[3]);
    const long double error=medium-(work-(H-H0));
    if(std::abs(error)>1e-10*std::max({1.L,std::abs(work),std::abs(H-H0)}))throw std::runtime_error("chemical work/medium entropy identity failed");
    long double msd=0;std::array<long double,3> mean{};
    for(int p=0;p<M;++p)for(int a=0;a<d;++a){long double v=displacement[p*d+a];msd+=v*v;mean[a]+=v;}
    // Ideal two-state mixing information relative to equal fractions: an
    // observational finite-fuel resource measure, not stored Hamiltonian energy.
    double information=0;const int64_t fuel=counts[3]+counts[4];
    for(int s=3;s<=4;++s)if(counts[s]>0)information+=counts[s]*std::log(2.*counts[s]/fuel);
    obs<<sample*10<<','<<M<<','<<NB<<','<<counts[1]<<','<<counts[3]<<','<<counts[4]<<','<<counts[0]<<','<<pairs<<','<<double(H)<<','<<double(work)<<','<<double(medium)<<','<<double(error)<<','<<proposals<<','<<reservoir_proposals;
    for(auto n:exchange)obs<<','<<n;
    obs<<','<<double(msd/M)<<','<<information;
    for(int a=0;a<d;++a)obs<<','<<double(mean[a]/M);
    for(int s=1;s<=4;++s)obs<<','<<hops[s];
    for(int s=0;s<4;++s)for(int n=0;n<=z;++n)obs<<','<<reactions[s][n];
    for(int s=0;s<=4;++s)for(auto n:profile[s])obs<<','<<n;
    for(int s=1;s<=4;++s)for(auto n:xflow[s])obs<<','<<n;
    for(int s=0;s<4;++s)for(auto n:rxn_x[s])obs<<','<<n;
    for(int s=0;s<4;++s)for(auto n:exchange_x[s])obs<<','<<n;
    obs<<'\n';obs.flush();
    if(sample==0||sample==samples/4||sample==samples/2||sample==samples||sample%5==0)snapshot(sample);
  };
  auto event=[&](){
    proposals++;double intensity=contacts*exchange_bound;
    for(int s=1;s<=4;++s)intensity+=lists[s].size()*bound[s];
    double choice=uniform()*intensity;int type=1;
    for(;type<=4;++type){const double w=lists[type].size()*bound[type];if(choice<w)break;choice-=w;}
    if(type==5){
      reservoir_proposals++;const int x=source=="uniform"?index(V):N*index(V/N);
      choice/=contacts;int kind=-1,newtype=cell[x];
      if(cell[x]==0){if(choice<kex*zF){kind=0;newtype=3;}else if(choice<kex*(zF+zW)){kind=2;newtype=4;}}
      else if(cell[x]==3&&choice<kex){kind=1;newtype=0;}
      else if(cell[x]==4&&choice<kex){kind=3;newtype=0;}
      if(kind>=0){exchange[kind]++;exchange_x[kind][x%N]++;medium+=(kind%2==0?1.:-1.)*(kind<2?logF:logW);set_type(x,newtype);}
      return;
    }
    if(lists[type].empty())throw std::runtime_error("selected empty physical type");
    choice/=lists[type].size();const int x=lists[type][index(lists[type].size())],n=nb[x];
    if(choice<D[type]){
      const int direction=index(z),y=neighbor[x][direction];if(cell[y]!=0)return;
      if(type==2&&uniform()>=hop[n])return;
      if(type==2){const int delta=int(nb[y])-1-n;pairs+=delta;medium-=eps*delta;
        for(int a=0;a<z;++a)nb[neighbor[x][a]]--;for(int a=0;a<z;++a)nb[neighbor[y][a]]++;}
      const int mid=macro_at[x];set_type(x,0);set_type(y,type);macro_at[x]=-1;macro_at[y]=mid;
      if(mid>=0){position[mid]=y;displacement[mid*d+direction/2]+=(direction%2==0?1:-1);}
      hops[type]++;if(direction/2==0){if(direction%2==0)xflow[type][x%N]++;else xflow[type][(x%N+N-1)%N]--;}
      return;
    }
    if(type>2)throw std::runtime_error("nonreactive species selected reaction");
    choice-=D[type];const bool B=type==2;int path=0,y=-1;
    double actual=B?bp[n]:ip[n];
    if(choice>=pbar[type]){path=1;choice-=pbar[type];y=neighbor[x][index(z)];
      if(cell[y]!=(B?3:4))return;actual=B?bd[n]:id[n];}
    if(choice>=actual)return;
    const int sign=B?-1:1;medium-=sign*(df+eps*n);NB+=sign;pairs+=sign*n;
    const int kind=(path?2:0)+(B?0:1);reactions[kind][n]++;rxn_x[kind][x%N]++;
    set_type(x,B?1:2);for(int a=0;a<z;++a)nb[neighbor[x][a]]+=sign;
    if(path)set_type(y,B?4:3);
  };
  auto waiting=[&]()->long double {double intensity=contacts*exchange_bound;
    for(int s=1;s<=4;++s)intensity+=lists[s].size()*bound[s];
    return intensity>0?-std::log(uniform())/intensity:std::numeric_limits<long double>::infinity();};
  long double next=waiting();
  for(int sample=0;sample<=samples;++sample){while(next<=sample*10.L){event();next+=waiting();}measure(sample);}
  return 0;
 } catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
