#ifndef libCV_image
#define libCV_image   

#include "geometry.h"
#include "mutil.h"
#include "util.h"

#define PIX3(r,g,b)  	(r+(g<<8)+(b<<16))
#define PIXR(val)	(val%256)
#define PIXG(val)	((val>>8)%256)
#define PIXB(val)	(val>>16)

typedef struct ImageSt {
	int rows, cols;
	int maxv, minv;
	int **pixels;
	char name[256];
	struct ImageSt *next;
} *Image;

Image CreateImage(int rows, int cols );

void SetImagePixel1( Image im, int row, int col, int val );

void SetImagePixel3( Image im, int row, int col, int r, int g, int b );

Image ReadPGMFile(char *filename);

Image ReadPGM(FILE *fp);

void WritePGM(char *name, Image image);

void ClearImage( Image out, int val );

void FreeImage( Image out );

Image ReadPPMFile( char *filename );

Image ReadPPM( FILE *fp );

void SkipComments(FILE *fp);

void WritePPM( char *name, Image image);

Image CopyImage( Image or );

Image ConvertImage1( Image im );

Image ConvertImage3( Image im );

char ImageIsGood( Image image );

void DrawPolygon( Polygon poly, Image out, int v );

void DrawEllipse( Ellipse ellipse, Image out, int v );
	
void FastLineDraw(int y0, int x0, int y1, int x1, Image out, int v );

Image CombineImagesVertically(Image im1, Image im2);

Image CombineImagesHorizontally(Image im1, Image im2);

Image GaussianBlurImage( Image im, float sigma );

void SplineImage( Image im, float **v2 );

int SplintImage( Image im, float **v2, float row, float col );

void WrapGaussianBlur1D( float *line, int l, int r, float sigma );

void GaussianBlur1D( float *line, int l, int r, float sigma );

int InterpolatePixelValue( Image im, float row, float col );

void AffineTransformImage( Image from, Image to, double **tr, double **it );

void FindImageLimits( Image im );

int ImageRangeDefined( Image im );

FVec GenerateImageHistogram( Image im );

Image EnhanceImage( Image im, int min, int max, float minh, float maxh );

Image PascalBlurImage( Image im, float sigma );

void DrawFVec(FVec sizes, int im_rmin, int im_cmin, int im_rmax, int im_cmax, int v, Image out );

void SeparableAffineTransform( Image im1, Image im2, double **TR, double **IT );

char RowColWithinImage( Image image, int row, int col );

Image SubtractImages( Image im1, Image im2, Image im3 );
Image MultiplyImages( Image im1, Image im2, Image im3 );
Image UnsharpMaskImage( Image im, float sigma );
Image SharpenImage( Image im, float val );
int RandomColor( int lum );
#endif
