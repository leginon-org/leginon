#include "util.h"

void FatalError(char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "Error: ");
    vfprintf(stderr, fmt, args);
    va_end(args);
    exit(1);
}

void Debug(int lvl, char *fmt, ...) {
	if ( libCV_debug < lvl ) return; 
	va_list args;
	va_start(args,fmt);
	vfprintf(stderr, fmt, args);
	va_end(args);
}

float RandomNumber( float min, float max) {
	float random = (float)rand() / RAND_MAX;
	random = random*(max-min) + min;
	return random;
}

float *CreateGaussianKernel( int ksize, float sigma ) {
	
	float *kernel = malloc(ksize*sizeof(float));
	
	int center = (int)(ksize/2);
	
	float sigma2sq = sigma*sigma*2;
	float norm = 1.0/(sqrt(2*PI)*sigma);
	float max = 0;
	
	int i;
	for (i=0;i<=center;i++) {
		int relPos = i - center;
		kernel[i] = exp(-(relPos*relPos)/sigma2sq)*norm;
	}
	
	for (i=center+1;i<ksize;++i) kernel[i] = kernel[ksize-i];
	for (i=0;i<ksize;++i) max+= kernel[i];
	for (i=0;i<ksize;++i) kernel[i] /= max;
	
	kernel += ksize/2;
 
	return kernel;
	
}

int FastLineIntegrate(int y0, int x0, int y1, int x1, int *pixels, int maxcol) {

	int dy = y1 - y0;
	int dx = x1 - x0;
	int stepx, stepy;
	int sum = 0;
	
    if (dy < 0) { dy = -dy;  stepy = -maxcol; } else { stepy = maxcol; }
    if (dx < 0) { dx = -dx;  stepx = -1; } else { stepx = 1; }
	dy <<= 1;
	dx <<= 1;

	y0 *= maxcol;
	y1 *= maxcol;
	sum += pixels[x0+y0];
	if (dx > dy) {
		int fraction = dy - (dx >> 1);
		while (x0 != x1) {
			if (fraction >= 0) {
				y0 += stepy;
				fraction -= dx;
			}
			x0 += stepx;
			fraction += dy;
			sum += pixels[x0+y0];
		}
	} else {
		int fraction = dx - (dy >> 1);
		while (y0 != y1) {
			if (fraction >= 0) {
				x0 += stepx;
				fraction -= dy;
			}
			y0 += stepy;
			fraction += dx;
			sum += pixels[x0+y0];
		}
	}
	
	return sum;

}

#ifdef CPUTIME
void Time( float *time ) {
	static float t0=0;
	if (t0 == 0) t0=CPUTIME;
	else { *time+=CPUTIME-t0; t0=0; }
}
#endif

void ISplint( int *v, float *v2, int n, float x, float *val ) {
	int klo, khi;
	float b, a;
	klo= x;
	khi= klo+1;
	a= khi-x;
	b= x-klo;
	*val=a*v[klo]+b*v[khi]+((a*a*a-a)*v2[klo]+(b*b*b-b)*v2[khi])*1.0/6.0;
}

void ISpline( int *v, int n, float *v2 ) {
	int i, k;
	float p, qn, un, *u;
	u = malloc(sizeof(float)*n);
	v2[0]=u[0]=0.0;
	for (i=1;i<n-1;i++) {
		p = 0.5*v2[i-1]+2.0;
		v2[i] = -0.5/p;
		u[i] =(v[i+1]-v[i])-(v[i]-v[i-1]);
		u[i] =(6.0*u[i]/2.0 - 0.5*u[i-1])/p;
	}
	qn=un=0.0;
	v2[n-1]=(un-qn*u[n-2])/(qn*v2[n-2]+1.0);
	for (k=n-2;k>=0;k--) v2[k]=v2[k]*v2[k+1]+u[k];
	free(u);
}

void FSplint( float *v, float *v2, int n, float x, float *val ) {
	int klo, khi;
	float b, a;
	klo= x;
	khi= klo+1;
	a= khi-x;
	b= x-klo;
	*val=a*v[klo]+b*v[khi]+((a*a*a-a)*v2[klo]+(b*b*b-b)*v2[khi])*1.0/6.0;
}

void FSpline( float *v, int n, float *v2 ) {
	int i, k;
	float p, qn, un, *u;
	u = malloc(sizeof(float)*n);
	v2[0]=u[0]=0.0;
	for (i=1;i<n-1;i++) {
		p = 0.5*v2[i-1]+2.0;
		v2[i] = -0.5/p;
		u[i] =(v[i+1]-v[i])-(v[i]-v[i-1]);
		u[i] =(6.0*u[i]/2.0 - 0.5*u[i-1])/p;
	}
	qn=un=0.0;
	v2[n-1]=(un-qn*u[n-2])/(qn*v2[n-2]+1.0);
	for (k=n-2;k>=0;k--) v2[k]=v2[k]*v2[k+1]+u[k];
	free(u);
}


double pythag( double a, double b ) {
	double absa = ABS(a);
	double absb = ABS(b);
	if ( absa > absb ) return absa*sqrt(1+(absb/absa)*(absb/absa));
	else return ( absb == 0.0 ? 0.0 : absb*(sqrt(1+absa/absb)) );
}

float MeanValue( float *A, int l, int r ) {
	float sum = 0; int i, size = r - l + 1;
	for (i=l;i<=r;i++) sum += A[i];
	sum = sum / size;
	return sum;
}

float StandardDeviation( float *A, int l, int r ) {
	float mean = MeanValue(A,l,r);
	float sum = 0; int i;
	for (i=l;i<=r;i++) sum += ABS( A[i] - mean );
	sum /= ( r - l + 1 );
	return sqrt(sum);
}

float LargestValue( float *array, int l, int r ) {
	int i; float max = array[l];
	for(i=l;i<=r;i++) max = MAX(max,array[i]);
	return max;
}

float SmallestValue( float *array, int l, int r ) {
	int i; float max = array[l];
	for(i=l;i<=r;i++) max = MIN(max,array[i]);
	return max;
}
