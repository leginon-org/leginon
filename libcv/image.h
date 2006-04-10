#include "util.h"
#include "mutil.h"
#include "ellipsefit.h"

#define PIX3(r,g,b)  	(r+(g<<8)+(b<<16))
#define PIXR(val)	(val%256)
#define PIXG(val)	((val>>8)%256)
#define PIXB(val)	(val>>16)

typedef struct ImageSt {
	int rows, cols;
	int maxv, minv;
	int **pixels;
	struct ImageSt *next;
} *Image;

Image CreateImage(int rows, int cols );
void FreeImage( Image out );
Image CopyImage( Image or );
void SetImagePixel1( Image im, int row, int col, int val );
void SetImagePixel3( Image im, int row, int col, int r, int g, int b );
void ClearImage1( Image out, int val );
void ClearImage3( Image out, int r, int g, int b);
void ConvertImage1( Image im );
void ConvertImage3( Image im );
Image CombineImagesVertically(Image im1, Image im2);
Image CombineImagesHorizontally(Image im1, Image im2);

Image ReadPGMFile(char *filename);
void WritePGM(char *name, Image image);
Image ReadPPMFile( char *filename );
void WritePPM( char *name, Image image);

void DrawPointStack( PointStack points, Image out, int r, int g, int b );
void DrawEllipse( Ellipse e, Image out, int r, int g, int b );
void FastLineDraw(int y0, int x0, int y1, int x1, Image out, int rv, int gv, int bv );
void DrawPoint(Image image, int row, int col, int size, int r, int g, int b );

void GaussianBlurImage( Image im, float sigma );
void PascalBlurImage( Image im, float sigma );
void SplineImage( Image im, float **v2 );
int SplintImage( Image im, float **v2, float row, float col );

void WrapGaussianBlur1D( float *line, int l, int r, float sigma );
int InterpolatePixelValue( Image im, float row, float col );
void AffineTransformImage( Image from, Image to, double **tr, double **it );
