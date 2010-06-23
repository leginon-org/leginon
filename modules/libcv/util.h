
#ifndef libCV_util
#define libCV_util 1

#include <sys/time.h>
#include <sys/types.h>
#include <time.h>
#include <stdlib.h>
#include <math.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

#ifndef ABS
#define ABS(x)		( (x) >  0  ? (x) : -(x))
#endif
#ifndef MAX
#define MAX(x,y)	( (x) > (y) ? (x) : (y))
#endif
#ifndef MIN
#define MIN(x,y)	( (x) < (y) ? (x) : (y))
#endif
#define BOUND(x,y,z)	MAX(x,MIN(y,z))
#define SIGN(a,b)	((b) >= 0.0 ? ABS(a) : -ABS(a))

#define TRUE	1
#define FALSE	0
#define PI	3.14159265358979
#define RAD	0.017453292519943295
#define DEG	57.295779513082323
#define TINY	1.0e-20;
#define MACHEPS	2.22045e-16
#define NaN	-91919191

void FatalError(char *fmt, ...);
void Debug(int lvl, char *fmt, ...);
float RandomNumber(float min, float max);
float *CreateGaussianKernel( int ksize, float sigma );
int FastLineIntegrate(int x0, int y0, int x1, int y1, int *pixels, int maxcol);
float LargestValue( float *array, int l, int r );
float SmallestValue( float *array, int l, int r );
void CreateDirectAffineTransform( float x1, float y1, float x2, float y2, float x3, float y3, float u1, float v1, float u2, float v2, float u3, float v3, double **TR,
double **IT );
void ISplint( int *v, float *v2, int n, float x, float *val );
void ISpline( int *v, int n, float *v2 );
void FSplint( float *v, float *v2, int n, float x, float *val );
void FSpline( float *v, int n, float *v2 );
double pythag( double a, double b );
float MeanValue( float *A, int l, int r );
float StandardDeviation( float *A, int l, int r );

#endif
