/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource				 |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#include <sfftw.h>
#include <srfftw.h>

typedef struct InfoStruct {
	double	minval;
	double	maxval;
	double	nminval;
	double	nmaxval;
	double	stddev;
	double	avg;
	double	scale;
	int n;
} Info;

void getFFT(int M, int N, int ** tpixels );
void getfft(gdImagePtr im_src);
int mrc_to_fftw_image(MRC *pMRC, int ** tpixels, int mask_radius, int minpix, int maxpix, int colormap);
double fftw_info(MRC *pMRC, Info *pInfo, int mask_radius);
double square(fftw_complex A);
