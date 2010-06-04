/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource				 |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#include "php.h"
#include "mrc.h"
#include "gd_unbundled.h"
#include "gd.h"
#include "gd_mrc.h"
#include "filter.h"
#include "fft3.h"

/* {{{ double square(fftw_complex C) */
double square(fftw_complex C) {
	return sqrt(C[0] * C[0] + C[1] * C[1]);
}
/* }}} */

/* {{{ int mrc_fftw(MRC *pMRC, int mask_radius) */
int mrc_fftw(MRC *pMRC, int mask_radius) {

	int i,j,ij,IJ;
	int nx,ny,nyh;
	int size,offset;
	float fmin,fmax;
	float fmean,stddev;
	double val,n,somme,somme2;
	double * in;
	float * data;
	fftw_complex *out;
	fftw_plan plan;

	nx = pMRC->header.nx;
	ny = pMRC->header.ny;

	val=n=somme=somme2=0;
	size = nx*ny;
	offset = (1+nx)*ny/2;
	nyh = (ny/2)+1;

	in = malloc ( sizeof ( double ) * size );
	data = (float *)pMRC->pbyData;

	for ( i = 0; i < size; i++ ) {
		in[i] = (float)data[i];
	}

	out = fftw_malloc ( sizeof ( fftw_complex ) * nx*nyh );

	plan = fftw_plan_dft_r2c_2d(nx, ny, in, out, FFTW_ESTIMATE);
	fftw_execute(plan);
	fftw_destroy_plan(plan);

	for (i = 0; i < nx; ++i) {
		for (j = 0; j < nyh; ++j) {
			ij = i*nyh + j;
			IJ = i*ny + j;
			val = square(out[ij]); 
			if (mask_radius > 0 && (
				(sqrt(i*i + j*j) < mask_radius) || 
				(sqrt((ny-i)*(ny-i) + j*j) < mask_radius) )) {
					continue;
			}

			fmin = MIN(fmin, val);
			fmax = MAX(fmax, val);
			somme  += val;
			somme2 += val*val;
			n++;
			
			if (i < nx/2 && j < ny/2) {
				// 1st quadrant
				data[offset - IJ -1] = val;
				// 4th quadrant
				data[offset + IJ] = val;
			}
			if ( i > nx/2 && j < ny/2) {
				// 2nd quadrant
				data[offset - IJ -1 + nx*ny] = val;
				// 3rd quadrant
				data[offset + IJ - nx*ny] = val;
			}
		}
	}

	if (n>0) {
		fmean = somme/n;
		stddev = sqrt((somme2 * n - somme * somme) / (n*n));
	}

	pMRC->header.amin = fmin;
	pMRC->header.amax = fmax;
	pMRC->header.amean = fmean;
	pMRC->header.rms = stddev;

	
	fftw_free(out);
	free(in);
	
}
/* }}} */


/* {{{	vim options
 * Local variables:
 * c-basic-offset: 4
 * End:
 * vim600: noet sw=4 ts=4 fdm=marker
 * vim<600: noet sw=4 ts=4
}}} */
