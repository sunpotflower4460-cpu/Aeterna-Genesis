// Independent local exclusion-fluid CTMC. No geometry labels enter the rates.
// Uniformization schedules null/accepted local events using a CONSTANT bound.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

struct Rates {
  double eps,df,mu,eta,ts,D,DI,DB,scale,pbar=0,dbar=0,total=0;
  int d,z;
  std::array<double,7> bp{},ip{},bd{},id{},hop{};
  Rates(double e,double f,double m,double h,double t,double mobility,double rate,int dim,double inert_mobility=-1.):
      eps(e),df(f),mu(m),eta(h),ts(t*e),D(std::max(mobility,inert_mobility<0?mobility:inert_mobility)),DI(inert_mobility<0?mobility:inert_mobility),DB(mobility),scale(rate),d(dim),z(2*dim) {
    if(e>0 || h<0 || mobility<0 || DI<0 || rate<0 || t<0 || t>1 || (d!=2&&d!=3))
      throw std::runtime_error("invalid physical parameters");
    for(int n=0;n<=z;++n) {
      ip[n]=scale; bp[n]=scale*std::exp(df+eps*n);
      id[n]=scale*eta*std::exp(-ts*n-mu/2);
      bd[n]=scale*eta*std::exp((eps-ts)*n+df+mu/2);
      hop[n]=std::exp(eps*n);
      pbar=std::max({pbar,ip[n],bp[n]});dbar=std::max({dbar,id[n],bd[n]});
    }
    total=D+pbar+dbar;
    if(!std::isfinite(total)||total<=0)throw std::runtime_error("invalid proposal bound");
  }
};

template<class T> void write_array(const std::filesystem::path &path,const std::vector<T>& v) {
  std::ofstream out(path,std::ios::binary);
  out.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(T));
  if(!out)throw std::runtime_error("snapshot write failed");
}

int main(int argc,char** argv) {
 try {
  if(argc==10 && std::string(argv[1])=="--rates") {
    Rates r(std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]),std::stod(argv[5]),
            std::stod(argv[6]),std::stod(argv[7]),std::stod(argv[8]),std::stoi(argv[9]));
    std::cout<<std::setprecision(17)<<"n,bp,ip,bd,id,hop,pbar,dbar,total\n";
    for(int n=0;n<=r.z;++n)std::cout<<n<<','<<r.bp[n]<<','<<r.ip[n]<<','<<r.bd[n]<<','
        <<r.id[n]<<','<<r.hop[n]<<','<<r.pbar<<','<<r.dbar<<','<<r.total<<'\n';
    return 0;
  }
  if(argc!=16)throw std::runtime_error("expected N d molecules T seed epsilon df mu eta ts_fraction D rate out initial_B_count D_I");
  const int N=std::stoi(argv[1]),d=std::stoi(argv[2]),M=std::stoi(argv[3]),B0=std::stoi(argv[14]);
  const double T=std::stod(argv[4]); const uint64_t seed=std::stoull(argv[5]);
  Rates r(std::stod(argv[6]),std::stod(argv[7]),std::stod(argv[8]),std::stod(argv[9]),
          std::stod(argv[10]),std::stod(argv[11]),std::stod(argv[12]),d,std::stod(argv[15]));
  int V=1;for(int a=0;a<d;++a)V*=N;
  const int samples=std::lround(T/10);
  if(N<3||M<1||M>=V||B0<0||B0>M||samples<0||std::abs(T-10*samples)>1e-8)
    throw std::runtime_error("invalid size/count or nonmultiple-of-10 horizon");
  const std::filesystem::path out=argv[13];
  // Frontend creates an immutable directory and recipe before invoking us.
  if(std::filesystem::exists(out/"series.csv"))throw std::runtime_error("refuse existing history");
  std::vector<std::array<int,6>> neighbors(V);
  for(int x=0;x<V;++x) {
    int jump=1;
    for(int a=0;a<d;++a) {
      int c=(x/jump)%N;
      neighbors[x][2*a]=c+1==N?x-(N-1)*jump:x+jump;
      neighbors[x][2*a+1]=c==0?x+(N-1)*jump:x-jump;
      jump*=N;
    }
  }
  std::mt19937_64 initial_rng(seed^0x9e3779b97f4a7c15ULL),rng(seed^0xd1b54a32d192ed03ULL);
  auto index=[&](int size){return std::uniform_int_distribution<int>(0,size-1)(rng);};
  // 52 bits plus an exactly representable half: strictly 0<U<1 in binary64.
  auto uniform=[&](){return ((rng()>>12)+.5)*0x1p-52;};
  std::vector<int32_t> permutation(V);std::iota(permutation.begin(),permutation.end(),0);
  for(int i=0;i<M;++i) {
    int j=std::uniform_int_distribution<int>(i,V-1)(initial_rng);
    std::swap(permutation[i],permutation[j]);
  }
  std::vector<int32_t> position(permutation.begin(),permutation.begin()+M),at(V,-1);
  std::vector<uint8_t> state(M),nb(V,0);
  std::vector<int64_t> displacement(M*d,0);
  for(int p=0;p<M;++p){at[position[p]]=p;state[p]=p<B0;}
  auto isB=[&](int x){return at[x]>=0&&state[at[x]]==1;};
  for(int x=0;x<V;++x)for(int a=0;a<r.z;++a)nb[x]+=isB(neighbors[x][a]);
  int64_t NB=B0,pairs=0;
  for(int x=0;x<V;++x)if(isB(x))pairs+=nb[x];pairs/=2;
  const long double H0=r.df*NB+r.eps*pairs;
  long double heat=0;
  uint64_t proposals=0,hops=0;
  std::array<std::array<int64_t,7>,4> reactions{}; // pBI,pIB,dBI,dIB
  std::array<std::array<std::array<int64_t,7>,7>,2> transitions{}; // I,B; source/destination nB
  auto snapshot=[&](int sample) {
    std::vector<uint8_t> cells(V,0);
    for(int p=0;p<M;++p)cells[position[p]]=1+state[p];
    const auto prefix=out/("state-"+std::to_string(sample));
    write_array(prefix.string()+"-cells.bin",cells);
    write_array(prefix.string()+"-positions.bin",position);
    write_array(prefix.string()+"-conformers.bin",state);
    write_array(prefix.string()+"-displacements.bin",displacement);
  };
  std::ofstream obs(out/"series.csv");obs<<std::setprecision(17);
  obs<<"time,molecules,B,pairs,H,work,heat,heat_budget_error,proposals,hops,msd";
  for(int a=0;a<d;++a)obs<<",mean_dx"<<a;
  for(int kind=0;kind<3;++kind)for(int n=0;n<=r.z;++n)obs<<",env_"<<kind<<'_'<<n;
  for(int kind=0;kind<4;++kind)for(int n=0;n<=r.z;++n)obs<<",rxn_"<<kind<<'_'<<n;
  for(int kind=0;kind<2;++kind)for(int a=0;a<=r.z;++a)for(int b=0;b<=r.z;++b)
    obs<<",hop_"<<kind<<'_'<<a<<'_'<<b;
  obs<<'\n';
  auto measure=[&](int sample) {
    int64_t count=0,actualB=0,actualPairs=0;
    std::array<std::array<int64_t,7>,3> environments{};
    for(int x=0;x<V;++x) {
      int n=0;for(int a=0;a<r.z;++a)n+=isB(neighbors[x][a]);
      if(n!=nb[x])throw std::runtime_error("neighbor cache disagrees with independent local count");
      int kind=at[x]<0?0:1+state[at[x]];
      environments[kind][n]++;
      if(at[x]>=0)count++;
      if(isB(x)){actualB++;actualPairs+=n;}
    }
    if(count!=M||actualB!=NB||actualPairs!=2*pairs)throw std::runtime_error("independent mass/pair budget failed");
    for(int p=0;p<M;++p)if(at[position[p]]!=p)throw std::runtime_error("particle identity lost");
    int64_t driven=0;for(int n=0;n<=r.z;++n)driven+=reactions[2][n]-reactions[3][n];
    const long double H=r.df*NB+r.eps*pairs,work=r.mu*driven,error=heat-(work-(H-H0));
    if(std::abs(error)>1e-10*std::max({1.L,std::abs(work),std::abs(H-H0)}))
      throw std::runtime_error("energy/work/heat identity failed");
    long double msd=0;std::array<long double,3> mean{};
    for(int p=0;p<M;++p)for(int a=0;a<d;++a){long double x=displacement[p*d+a];msd+=x*x;mean[a]+=x;}
    obs<<sample*10<<','<<M<<','<<NB<<','<<pairs<<','<<double(H)<<','<<double(work)<<','<<double(heat)
       <<','<<double(error)<<','<<proposals<<','<<hops<<','<<double(msd/M);
    for(int a=0;a<d;++a)obs<<','<<double(mean[a]/M);
    for(int k=0;k<3;++k)for(int n=0;n<=r.z;++n)obs<<','<<environments[k][n];
    for(int k=0;k<4;++k)for(int n=0;n<=r.z;++n)obs<<','<<reactions[k][n];
    for(int k=0;k<2;++k)for(int a=0;a<=r.z;++a)for(int b=0;b<=r.z;++b)obs<<','<<transitions[k][a][b];
    obs<<'\n';obs.flush();
    if(sample==0||sample==samples/4||sample==samples/2||sample==samples||sample%5==0)snapshot(sample);
  };
  auto event=[&]() {
    proposals++;
    const int p=index(M),x=position[p],n=nb[x];const bool B=state[p];
    double choice=uniform()*r.total;
    if(choice<r.D) {
      int direction=index(r.z),y=neighbors[x][direction];
      if(at[y]>=0)return;
      const double acceptance=B?r.DB/r.D*r.hop[n]:r.DI/r.D;
      if((B||acceptance<1.)&&uniform()>=acceptance)return;
      int destination=nb[y]-int(B); // remove departing B before counting destination contacts
      transitions[int(B)][n][destination]++;
      if(B) {
        int delta=destination-n;pairs+=delta;heat-=r.eps*delta;
        for(int a=0;a<r.z;++a)nb[neighbors[x][a]]--;
        for(int a=0;a<r.z;++a)nb[neighbors[y][a]]++;
      }
      at[x]=-1;at[y]=p;position[p]=y;hops++;
      displacement[p*d+direction/2]+=(direction%2==0?1:-1);
      return;
    }
    choice-=r.D;int path=0;double actual=B?r.bp[n]:r.ip[n];
    if(choice>=r.pbar){path=1;choice-=r.pbar;actual=B?r.bd[n]:r.id[n];}
    if(choice>=actual)return;
    const int sign=B?-1:1;
    const double deltaH=sign*(r.df+r.eps*n);
    heat+=-deltaH+(path?r.mu*(-sign):0.);
    reactions[(path?2:0)+(B?0:1)][n]++;
    NB+=sign;pairs+=sign*n;state[p]=!B;
    for(int a=0;a<r.z;++a)nb[neighbors[x][a]]+=sign;
  };
  long double next=-std::log(uniform())/(M*r.total);
  for(int sample=0;sample<=samples;++sample) {
    while(next<=sample*10.L){event();next+=-std::log(uniform())/(M*r.total);}
    measure(sample);
  }
  return 0;
 } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
