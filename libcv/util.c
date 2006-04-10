#include "defs.h"

void FatalError(char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "Error: ");
    vfprintf(stderr, fmt, args);
    fprintf(stderr,"\n");
    va_end(args);
    exit(1);
}

float randomnumber( ) {
	return (float)rand() / RAND_MAX;
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

float LargestValue( float *array, int l, int r ) {
	if ( l == r ) return array[l];
	float u, v;
	int m = (l+r)/2;
	u = LargestValue( array, l, m );
	v = LargestValue( array, m+1, r );
	if ( u > v ) return u;
	else return v;
}

void Time( float *time ) {
	static float t0=0;
	if (t0 == 0) t0=CPUTIME;
	else { *time+=CPUTIME-t0; t0=0; }
}

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

void CreateDirectAffineTransform( float x1, float y1, float x2, float y2, float x3, float y3, float u1, float v1, float u2, float v2, float u3, float v3, double **TR,
double **IT ) {

	if (IT != NULL ) {
		 float det = 1.0/(u1*(v2-v3)-v1*(u2-u3)+(u2*v3-u3*v2));
		 IT[0][0] = ((v2-v3)*x1+(v3-v1)*x2+(v1-v2)*x3)*det;
		 IT[0][1] = ((v2-v3)*y1+(v3-v1)*y2+(v1-v2)*y3)*det;
		 IT[0][2] = 0;
		 IT[1][0] = ((u3-u2)*x1+(u1-u3)*x2+(u2-u1)*x3)*det;
		 IT[1][1] = ((u3-u2)*y1+(u1-u3)*y2+(u2-u1)*y3)*det;
		 IT[1][2] = 0;
		 IT[2][0] = ((u2*v3-u3*v2)*x1+(u3*v1-u1*v3)*x2+(u1*v2-u2*v1)*x3)*det;
		 IT[2][1] = ((u2*v3-u3*v2)*y1+(u3*v1-u1*v3)*y2+(u1*v2-u2*v1)*y3)*det;
		 IT[2][2] = 1;
	}
	
	if (TR != NULL ) {
		float det = 1.0/(x1*(y2-y3)-y1*(x2-x3)+(x2*y3-x3*y2));
		TR[0][0] = ((y2-y3)*u1+(y3-y1)*u2+(y1-y2)*u3)*det;
		TR[0][1] = ((y2-y3)*v1+(y3-y1)*v2+(y1-y2)*v3)*det;
		TR[0][2] = 0;
		TR[1][0] = ((x3-x2)*u1+(x1-x3)*u2+(x2-x1)*u3)*det;
		TR[1][1] = ((x3-x2)*v1+(x1-x3)*v2+(x2-x1)*v3)*det;
		TR[1][2] = 0;
		TR[2][0] = ((x2*y3-x3*y2)*u1+(x3*y1-x1*y3)*u2+(x1*y2-x2*y1)*u3)*det;
		TR[2][1] = ((x2*y3-x3*y2)*v1+(x3*y1-x1*y3)*v2+(x1*y2-x2*y1)*v3)*det;
		TR[2][2] = 1;
	}
	
}

void ComputeEllipseTransform( Ellipse e1, Ellipse e2, double **TR, double **IT ) {

	float er1 = e1->erow, ec1 = e1->ecol;
	float maj1 = e1->majaxis;
	float min1 = e1->minaxis;
	float c1 = cos(e1->phi), s1 = sin(e1->phi);
	float er2 = e2->erow, ec2 = e2->ecol;
	float maj2 = e2->majaxis;
	float min2 = e2->minaxis;
	float c2 = cos(e2->phi), s2 = sin(e2->phi);
		
	float x1 = er1-min1*s1, y1 = ec1+min1*c1;
	float x2 = er1-maj1*c1, y2 = ec1-maj1*s1;
	float x3 = er1, y3 = ec1;
	float u1 = er2-min2*s2, v1 = ec2+min2*c2;
	float u2 = er2-maj2*c2, v2 = ec2-maj2*s2;
	float u3 = er2, v3 = ec2; 
	
	CreateDirectAffineTransform(x1,y1,x2,y2,x3,y3,u1,v1,u2,v2,u3,v3,TR,IT);
	
}	

double pythag( double a, double b ) {
	double absa = ABS(a);
	double absb = ABS(b);
	if ( absa > absb ) return absa*sqrt(1+(absb/absa)*(absb/absa));
	else return ( absb == 0.0 ? 0.0 : absb*(sqrt(1+absa/absb)) );
}
