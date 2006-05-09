
#include <stdlib.h>
#include <math.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <time.h>

#ifndef ABS
#define ABS(x)    		( (x) >  0  ? (x) : -(x))
#endif
#ifndef MAX
#define MAX(x,y)		( (x) > (y) ? (x) : (y))
#endif
#ifndef MIN
#define MIN(x,y)		( (x) < (y) ? (x) : (y))
#endif
#define BOUND(x,y,z)	MAX(x,MIN(y,z))
#define SIGN(a,b)		((b) >= 0.0 ? ABS(a) : -ABS(a))
#define PIX3(r,g,b)		(r+(g<<8)+(b<<16))
#define PIXR(val)		(val%256)
#define PIXG(val)		((val>>8)%256)
#define PIXB(val)		(val>>16)
#define CPUTIME			(getrusage(RUSAGE_SELF,&ruse),ruse.ru_utime.tv_sec+ruse.ru_stime.tv_sec+1e-6*(ruse.ru_utime.tv_usec+ruse.ru_stime.tv_usec))

#define TRUE	1
#define FALSE	0
#define PI	3.14159265358979
#define RAD	0.017453292519943295
#define DEG	57.295779513082323
#define TINY	1.0e-20;
#define MACHEPS	2.22045e-16

struct rusage ruse;

typedef struct MatchSt {
	struct DescriptorSt *p1, *p2;
} *Match;

typedef struct ImageSt {
	int rows, cols;
	int maxv, minv;
	int **pixels;
	struct ImageSt *next;
} *Image;

typedef struct FArraySt {
	float **values;
	int maxrow, maxcol;
	int minrow, mincol;
	int rmaxrow, rmaxcol;
	int rminrow, rmincol;
} *FArray;

typedef struct FVecSt {
	float *values;
	int max_r, max_l, r, l;
} *FVec;

typedef struct PStackSt {
	void **items;
	int stacksize, realsize, cursor;
} *PStack;

typedef struct FStackSt {
	float *items;
	int stacksize, realsize;
} *FStack;

typedef struct IStackSt {
	int *items, start, end, size;
} *IStack;

typedef struct PointStackSt {
	struct PointSt *items;
	int stacksize, realsize, cursor;
} *PointStack;

typedef struct PointSt {
	float row, col;
} *Point;

typedef struct RegionSt {

	float row, col, ori, scale;
	
	double A,B,C,D,E,F,maj,min,phi;
	double minr, maxr, minc, maxc;
	
	struct ImageSt *image;
	
	struct PointStackSt *sizes;
	struct PointStackSt *border;
	int stable, root;
	
} *Region;

typedef struct DescriptorSt {
	float row, col, scale, ori;
	int descriptortype;
	int descriptorlength;
	float *descriptor;
} *Descriptor;

typedef struct EllipseSt {
	double erow, ecol, majaxis, minaxis, phi;
	double A,B,C,D,E,F;
	double minr, maxr, minc, maxc;
} *Ellipse;

char FindMSERegions( Image image, PStack Regions, float minsize, float maxsize, float minperiod, float minstable );

Image CreateImage(int rows, int cols );
void SetImagePixel1( Image im, int row, int col, int val );
void SetImagePixel3( Image im, int row, int col, int r, int g, int b );
Image ReadPGMFile( char *filename );
void WritePGM(char *name, Image image);
void ClearImage( Image out, int val );
void FreeImage( Image out );
Image ReadPPMFile( char *filename );
void WritePPM( char *name, Image image);
Image CopyImage( Image or );
Image ConvertImage1( Image im );
Image ConvertImage3( Image im );
char ImageGood( Image image );
void DrawPointStack( PointStack points, Image out, int v );
void DrawEllipse( Ellipse e, Image out, int v );
void FastLineDraw(int y0, int x0, int y1, int x1, Image out, int v );
void AffineTransformImage( Image from, Image to, double **tr, double **it );
void FindImageLimits( Image im );
int ImageRangeDefined( Image im );
FVec GenerateImageHistogram( Image im );
Image EnhanceImage( Image im, int min, int max, float minh, float maxh );
void WrapGaussianBlur1D( float *line, int l, int r, float sigma );

int **AllocIMatrix(int rows, int cols, int rowoffset, int coloffset);
int **FreeIMatrix( int **matrix, int roff, int coff );
float **AllocFMatrix(int rows, int cols, int rowoffset, int coloffset);
float **FreeFMatrix( float **matrix, int roff, int coff );
double **AllocDMatrix(int rows, int cols, int rowoffset, int coloffset);
double **FreeDMatrix( double **matrix, int roff, int coff );
void CopyDMatrix( double **FROM, double **TO, int minr, int minc, int maxr, int maxc );

FArray NewFArray( int minrow, int mincol, int maxrow, int maxcol );
FArray ResizeFArray( FArray array, int newminrow, int newmincol, int newmaxrow, int newmaxcol );
void SetFArray( FArray array, int row, int col, float val );
float GetFArray( FArray array, int row, int col );
int FArrayCols( FArray array );
int FArrayRows( FArray array );
char FArrayGood( FArray array );
void InitFArrayScalar( FArray array, float val );
void CopyCArrayIntoFArray( FArray array, float **m, int lr, int lc, int rr, int rc );
FArray FreeFArray( FArray array );

FVec NewFVec( int l, int r );
void SetFVec( FVec vec, int k, float val );
void ResizeFVec( FVec vec, int newl, int newr );
float GetFVec( FVec vec, int k );
FVec FreeFVec( FVec vec );
char FVecGood( FVec vec );
void CopyCArrayIntoFVec( FVec vec, float *v, int ol, int or );
void PrintFVec( FVec vec );

PStack NewPStack(int size);
void PushPStack( PStack stack, void *pointer );
void *PopPStack( PStack stack );
char PStackEmpty( PStack stack );
PStack FreePStack( PStack stack );
char PStackCycle( PStack stack );
void *CyclePStack( PStack stack );

FStack NewFStack(int size);
void PushFStack( FStack stack, float value );
float PopFStack( FStack stack );
char PStackGood( PStack stack );
char FStackGood( FStack stack );
char FStackEmpty( FStack stack );
void FreeFStack( FStack stack );

PointStack NewPointStack( int size );
void PushPointStack( PointStack stack, int row, int col );
Point PopPointStack( PointStack stack );
char PointStackEmpty( PointStack stack );
int PointStackSize( PointStack stack );
char PointStackGood( PointStack stack );
char PointStackCycle( PointStack stack );
Point CyclePointStack( PointStack stack );
void FreePointStack( PointStack stack );
PointStack CopyPointStack( PointStack stack );

IStack NewIStack( int size );
void PushIStack( IStack stack, int value );
int PopIStack( IStack stack );

Region NewRegion( Ellipse e, Image im, PointStack vec, PointStack border, int stable, int region );
void RegionsToDescriptors( PStack Regions, PStack descriptors, int o1, int o2, int o3, int o4, int d1, int pb, int ob, int d2 );
void DetermineMajorOrientations( Region key, PStack Regions, FStack orientations );
void PrintSIFTDescriptors( char *name, PStack descriptors );
float *CreateSIFTDescriptor( Image patch, int pb, int ob );
float *CreatePCADescriptor( Image patch );
void GenerateGradientOrientationBins( Region key, Image im, float *bins );
void RegionToPatch( Region key, Image patch );
Descriptor NewDescriptor( Region key, int dlength, char dtype, float *d );
void OrientRegionsAsClusters( PStack Regions );
void GenerateClusterBins( Region key, PStack keys, float *bins );
void PrintRegions( char *name, PStack Regions );
void DrawDescriptor( Descriptor d, Image out );
void DrawRegion( Region key );
void DrawOrientations( float *bins, Image out, float ori );
void PlotNeighborClusters( Region key, PStack keys, Image out );

Ellipse CalculateAffineEllipse( PointStack pixels, float scale );
void ComputeEllipseTransform( Ellipse e1, Ellipse e2, double **TR, double **IT );

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

void FindMatches(PStack k1, PStack k2, PStack matches, int bound );
void ScreenMatches( PStack matches, double **transform);

float FindArea( FArray array );

void EllipseC( Ellipse e, double maj, double min, double cr, double cc, double phi, double mod );
void FindLineIntersection( int x1, int y1, int x2, int y2, int u1, int v1, int u2, int v2, int *xint, int *yint );
