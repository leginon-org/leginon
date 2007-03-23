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
	if ( 0 < lvl ) return; 
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
