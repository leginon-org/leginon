/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource				 |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#include <sfftw.h>
#include <srfftw.h>

void getFFT(int M, int N, int ** tpixels );
void getfft(gdImagePtr im_src);
int mrc_to_fftw_image(MRC *pMRC, int ** tpixels, int mask_radius, int minpix, int maxpix, int colormap);
double square(fftw_complex A);
