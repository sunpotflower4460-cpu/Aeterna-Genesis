// Narrow accelerator for sb_universe's e=0, two-complex-field polynomial.
// No clipping, objects, labels, stopping gates, or spatially selected forces.
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>
using State = std::array<std::vector<double>, 8>;
int main(int argc, char **argv) {
  if (argc != 13) return 2;
  int n=std::stoi(argv[1]), d=std::stoi(argv[2]), steps=std::stoi(argv[5]), stride=std::stoi(argv[6]);
  double c=std::stod(argv[3]), dt=std::stod(argv[4]), lam=std::stod(argv[7]), m2=std::stod(argv[8]), g=std::stod(argv[9]);
  bool convex=std::stoi(argv[10]);
  size_t size=1; for(int a=0;a<d;++a) size*=n;
  State u; for(auto &x:u)x.resize(size);
  std::ifstream input(argv[11],std::ios::binary);
  for(auto &x:u)input.read(reinterpret_cast<char*>(x.data()),size*sizeof(double));
  if(!input)throw std::runtime_error("incomplete input state");
  std::filesystem::path out=argv[12]; std::filesystem::create_directories(out);
  std::array<std::vector<double>,4> f; for(auto &x:f)x.resize(size);
  auto force=[&]() {
    #pragma omp parallel for schedule(static) if(size>100000)
    for(size_t i=0;i<size;++i) {
      double s0=u[0][i]*u[0][i]+u[1][i]*u[1][i], s1=u[2][i]*u[2][i]+u[3][i]*u[3][i];
      for(int q=0;q<4;++q) {
        double s=q<2?s0:s1, other=q<2?s1:s0;
        double v=convex ? (lam+m2+lam*s) : (m2+lam*(s-1)*(3*s-1));
        double lap=-2*d*u[q][i]; size_t jump=1;
        for(int a=0;a<d;++a) {
          size_t coord=(i/jump)%n;
          size_t ip=coord+1==size_t(n)?i-(n-1)*jump:i+jump;
          size_t im=coord==0?i+(n-1)*jump:i-jump;
          lap+=u[q][ip]+u[q][im]; jump*=n;
        }
        f[q][i]=c*c*lap-(v+g*other)*u[q][i];
      }
    }
  };
  auto snapshot=[&](int step) {
    std::ofstream file(out/("state-"+std::to_string(step)+".bin"),std::ios::binary);
    for(auto &x:u)file.write(reinterpret_cast<char*>(x.data()),size*sizeof(double));
    if(!file)throw std::runtime_error("snapshot write failed");
  };
  std::ofstream obs(out/"series.csv");obs<<std::setprecision(17);
  obs<<"step,time,energy,q1,q2,mean_s1,mean_s2,var_s1,var_s2,cov_s1_s2,max_s1,max_s2,finite\n";
  auto measure=[&](int step) {
    long double E=0,Q0=0,Q1=0,S0=0,S1=0,S00=0,S11=0,S01=0; double max0=0,max1=0; bool finite=true;
    for(size_t i=0;i<size;++i) {
      double s0=u[0][i]*u[0][i]+u[1][i]*u[1][i],s1=u[2][i]*u[2][i]+u[3][i]*u[3][i];
      S0+=s0;S1+=s1;S00+=s0*s0;S11+=s1*s1;S01+=s0*s1;max0=std::max(max0,s0);max1=std::max(max1,s1);
      Q0+=2*(u[0][i]*u[5][i]-u[1][i]*u[4][i]);Q1+=2*(u[2][i]*u[7][i]-u[3][i]*u[6][i]);
      E+=g*s0*s1;
      for(double s:{s0,s1})E+=convex ? ((lam+m2)*s+.5*lam*s*s) : (lam*s*(s-1)*(s-1)+m2*s);
      for(int q=0;q<4;++q) {
        E+=u[q+4][i]*u[q+4][i];size_t jump=1;
        for(int a=0;a<d;++a) {
          size_t ip=(i/jump)%n+1==size_t(n)?i-(n-1)*jump:i+jump;
          double delta=u[q][ip]-u[q][i];E+=c*c*delta*delta;jump*=n;
        }
        finite=finite&&std::isfinite(u[q][i])&&std::isfinite(u[q+4][i]);
      }
    }
    long double a=S0/size,b=S1/size;
    obs<<step<<','<<step*dt<<','<<double(E/size)<<','<<double(Q0/size)<<','<<double(Q1/size)<<','<<double(a)<<','<<double(b)<<','<<double(S00/size-a*a)<<','<<double(S11/size-b*b)<<','<<double(S01/size-a*b)<<','<<max0<<','<<max1<<','<<finite<<'\n';obs.flush();
  };
  force(); measure(0);snapshot(0);
  for(int k=1;k<=steps;++k) {
    #pragma omp parallel for schedule(static) if(size>100000)
    for(size_t i=0;i<size;++i)for(int q=0;q<4;++q) {
      u[q+4][i]+=.5*dt*f[q][i];u[q][i]+=dt*u[q+4][i];
    }
    force();
    #pragma omp parallel for schedule(static) if(size>100000)
    for(size_t i=0;i<size;++i)for(int q=0;q<4;++q)u[q+4][i]+=.5*dt*f[q][i];
    if(k%stride==0||k==steps)measure(k);
    if(k==steps/5||k==steps/2||k==steps)snapshot(k);
  }
}
