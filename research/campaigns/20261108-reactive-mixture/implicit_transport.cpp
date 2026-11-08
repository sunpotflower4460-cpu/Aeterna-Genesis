// Conservative periodic Scharfetter-Gummel backward Euler on independent lines.
// Shared diffusivity; valence is the number of conserved building blocks.
// No clipping, masks, selected geometry, source/sink, or reaction logic.
#include <cmath>
#include <vector>
static double B(double x) {
  if(std::abs(x)<1e-6)return 1-x/2+x*x/12;
  return x/std::expm1(x);
}
static void tri(const std::vector<double>&a,const std::vector<double>&b,
                const std::vector<double>&c,const std::vector<double>&r,std::vector<double>&x) {
  int n=b.size();std::vector<double> cp(n),dp(n);
  cp[0]=c[0]/b[0];dp[0]=r[0]/b[0];
  for(int i=1;i<n;++i) {
    double pivot=b[i]-a[i]*cp[i-1];
    cp[i]=(i==n-1?0:c[i]/pivot);dp[i]=(r[i]-a[i]*dp[i-1])/pivot;
  }
  x.resize(n);x[n-1]=dp[n-1];
  for(int i=n-2;i>=0;--i)x[i]=dp[i]-cp[i]*x[i+1];
}
extern "C" int transport_axis(double* c,const double* phi,int n,int d,int axis,
                              double chi,double valence,double D,double dt,double dx) {
  if(n<3||d<1||d>3||axis<0||axis>=d||dt<0||dx<=0)return 1;
  long size=1,jump=1;for(int a=0;a<d;++a)size*=n;for(int a=0;a<axis;++a)jump*=n;
  long lines=size/n;double tau=D*dt/(dx*dx);int bad=0;
  #pragma omp parallel for schedule(static) reduction(|:bad) if(lines>100)
  for(long line=0;line<lines;++line) {
    long start=(line/jump)*jump*n+line%jump;
    std::vector<double>a(n),b(n),u(n),r(n),pot(n),x,z,rhs(n,0.);
    for(int i=0;i<n;++i){pot[i]=-valence*chi*phi[start+i*jump];r[i]=c[start+i*jump];}
    for(int i=0;i<n;++i) {
      double left=pot[i]-pot[(i+n-1)%n],right=pot[(i+1)%n]-pot[i];
      a[i]=-tau*B(left);u[i]=-tau*B(-right);
      b[i]=1+tau*(B(right)+B(-left));
    }
    // Sherman-Morrison: corners alpha=A[0,n-1], beta=A[n-1,0].
    double alpha=a[0],beta=u[n-1],gamma=-b[0];
    a[0]=0;u[n-1]=0;b[0]-=gamma;b[n-1]-=alpha*beta/gamma;
    tri(a,b,u,r,x);rhs[0]=gamma;rhs[n-1]=beta;tri(a,b,u,rhs,z);
    double factor=(x[0]+alpha/gamma*x[n-1])/(1+z[0]+alpha/gamma*z[n-1]);
    for(int i=0;i<n;++i) {
      double value=x[i]-factor*z[i];bad|=(!std::isfinite(value)||value<0);
      c[start+i*jump]=value;
    }
  }
  return bad?2:0;
}
