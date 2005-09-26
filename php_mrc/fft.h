/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource				 |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#include <sfftw.h>
#include <srfftw.h>

typedef fftw_real ** fftw2d_real_ptr;
void gd_fftw(gdImagePtr im_src, int mask_radius);
int mrc_fftw(MRC *pMRC, int mask_radius);

double square(fftw_complex A);
void fftw2d(fftw_real **in, fftw_complex *out, int M, int N);
fftw2d_real_ptr fftw2d_alloc(int M, int N);
void fftw2d_free(fftw_real **in); 
