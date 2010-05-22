/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource				 |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#include <fftw3.h>

double square(fftw_complex A);
int mrc_fftw(MRC *pMRC, int mask_radius);

