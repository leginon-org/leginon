
#include <sys/time.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <time.h>

#define ABS(x)    	(((x) > 0) ? (x) : (-(x)))
#define MAX(x,y)	(((x) > (y)) ? (x) : (y))
#define MIN(x,y)	(((x) < (y)) ? (x) : (y))
#define SIGN(a,b)	((b) >= 0.0 ? ABS(a) : -ABS(a))
#define CPUTIME	(getrusage(RUSAGE_SELF,&ruse),ruse.ru_utime.tv_sec+ruse.ru_stime.tv_sec+1e-6*(ruse.ru_utime.tv_usec+ruse.ru_stime.tv_usec))
#define TRUE	1
#define FALSE	0
#define PI		3.14159265358979
#define RAD		0.017453292519943295
#define DEG		57.295779513082323
#define TINY	1.0e-20;
#define MACHEPS	2.22045e-16

struct rusage ruse;

void FatalError(char *fmt, ...);
float randomnumber();
float *CreateGaussianKernel( int ksize, float sigma );
int FastLineIntegrate(int x0, int y0, int x1, int y1, int *pixels, int maxcol);
float LargestValue( float *array, int l, int r );
void Time( float *time );
void CreateDirectAffineTransform( float x1, float y1, float x2, float y2, float x3, float y3, float u1, float v1, float u2, float v2, float u3, float v3, double **TR,
double **IT );
void ISplint( int *v, float *v2, int n, float x, float *val );
void ISpline( int *v, int n, float *v2 );
void FSplint( float *v, float *v2, int n, float x, float *val );
void FSpline( float *v, int n, float *v2 );
double pythag( double a, double b );
