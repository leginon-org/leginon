/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource				 |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#include "php.h"
#include "mrc.h"
#include "gd.h"
#include "gd_mrc.h"
#include "filter.h"
#include "fft.h"
#include <sfftw.h>
#include <srfftw.h>



/* {{{ double square(fftw_complex C) */
double square(fftw_complex C) {
		return sqrt(C.re * C.re + C.im * C.im);
}
/* }}} */

/* {{{ int mrc_fftw(MRC *pMRC, int mask_radius) */
int mrc_fftw(MRC *pMRC, int mask_radius) {

	int i,j,ij=0;
	int IJ;

	int M = pMRC->header.nx;
	int N = pMRC->header.ny;
	int mode=pMRC->header.mode;
	int nrows = M ;
	int ncolumns = 2*(N/2+1) ;
	int offset = (1+M)*N/2;
	
	float val, fmin, fmax, fmean, stddev;
	double somme, somme2, n;

	rfftwnd_plan plan;
	fftw_complex *A;
	fftw2d_real_ptr a;
	fftw_real *data_array;


	a = fftw2d_alloc(M,N);

	A = (fftw_complex*) &a[0][0];

	switch (mode) {
	 case MRC_MODE_BYTE:
         {
		data_array = (fftw_real *)((char *)pMRC->pbyData);
		break;
	 }
	 case MRC_MODE_SHORT:
         {
		data_array = (fftw_real *)((short *)pMRC->pbyData);
		break;
	 }
	 case MRC_MODE_UNSIGNED_SHORT:
         {
		data_array = (fftw_real *)((unsigned short *)pMRC->pbyData);
		break;
	 }
	 case MRC_MODE_FLOAT:
         {
		data_array = (fftw_real *)((float *)pMRC->pbyData);
		break;
         }
	}

	for (i = 0; i < M; i++) {
		for (j = 0; j < N; j++) {
			ij = i*N + j;
				a[i][j] = (fftw_real)(data_array[ij]);
		}
	}

	fftw2d(a, A, M, N);
	for (i = 0; i < M; ++i) {
		for (j = 0; j < N/2+1; ++j) {
			ij = i*(N/2+1) + j;
			IJ = i*N +j;
			val = square(A[ij]); 
			if (mask_radius > 0 && (
				(sqrt(i*i + j*j) < mask_radius) || 
				(sqrt((N-i)*(N-i) + j*j) < mask_radius) )) {
					continue;
			}
			fmin = MIN(fmin, val);
			fmax = MAX(fmax, val);
			somme  += val;
			somme2 += val*val;
			n++;

			
			if (i < M/2 && j < N/2) {
				// 1st quadrant
				data_array[offset - IJ -1] = val;
				// 4th quadrant
				data_array[offset + IJ] = val;
			}
			if ( i > M/2 && j < N/2) {
				// 2nd quadrant
				data_array[offset - IJ -1 + M*N] = val;
				// 3rd quadrant
				data_array[offset + IJ - M*N] = val;
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


	fftw2d_free(a);
}
/* }}} */

/* {{{ void fftalloc(fftw_real **in, int M, int N) */
// void fftalloc(fftw_real **in, int M, int N) {
fftw2d_real_ptr fftw2d_alloc(int M, int N) {
	int	i=0,
		nrows = M,
		ncolumns = 2*(N/2+1) ;
	fftw_real **in = (fftw_real **)malloc(nrows * sizeof(fftw_real *));
	in[0] = (fftw_real *)malloc(nrows * ncolumns * sizeof(fftw_real));
	for(i = 1; i < nrows; i++)
		in[i] = in[0] + i * ncolumns;
	return in;
}
/* }}} */

/* {{{ void fftw2d(fftw_real **in, fftw_complex *out, int M, int N) */
void fftw2d(fftw_real **in, fftw_complex *out, int M, int N) {
	rfftwnd_plan plan;
	plan = rfftw2d_create_plan(M, N, FFTW_REAL_TO_COMPLEX, FFTW_ESTIMATE | FFTW_IN_PLACE);
	rfftwnd_one_real_to_complex(plan, &in[0][0], NULL);
	rfftwnd_destroy_plan(plan);
}
/* }}} */

/* {{{ void fftw2d_free(fftw_real **in) */
void fftw2d_free(fftw_real **in) {
	int i;
	if (in) {
		free(in[0]);
		free(in);
    }
}
/* }}} */

/* {{{ void gd_fftw(gdImagePtr im_src, int mask_radius) */
void gd_fftw(gdImagePtr im_src, int mask_radius) {
	float val,
		scale,
		stddev;
	int densitymax = densityMAX;
	int i, j, ij;
	int M, N;
	int ** tpixels;
	double somme, somme2, n;

	rfftwnd_plan plan;
	fftw2d_real_ptr a;
	fftw_complex *A;

	tpixels = im_src->tpixels;

	M = im_src->sx;
	N = im_src->sy;

	a = fftw2d_alloc(M,N);
	A = (fftw_complex*) &a[0][0];

	for (i = 0; i < M; ++i)
          for (j = 0; j < N; ++j) {
             a[i][j] = (fftw_real)getDensity(tpixels[j][i]);
          }

	fftw2d(a, A, M, N);

	for (i = 0; i < M; ++i) {
          for (j = 0; j < N/2+1; ++j) {
			ij = i*(N/2+1) + j;
			val = square(A[ij]);
			if (mask_radius > 0 && (
				(sqrt(i*i + j*j) < mask_radius) || 
				(sqrt((N-i)*(N-i) + j*j) < mask_radius) )) {
					continue;
			}
			somme  += val;
			somme2 += val*val;
			n++;
		}
	}

	if (n>0) {
		stddev = sqrt((somme2 * n - somme * somme) / (n*n));
	}

	scale = 6*stddev;

	for (i = 0; i < M; ++i) {
          for (j = 0; j < N/2+1; ++j) {
			ij = i*(N/2+1) + j;
			val = square(A[ij]); 
			val = val/scale*densitymax;

			if (mask_radius > 0 && (
				(sqrt(i*i + j*j) < mask_radius) || 
				(sqrt((N-i)*(N-i) + j*j) < mask_radius) )) {
				 val = 0;
			}
			if (i <= M/2 && j <= N/2) {
				tpixels[j+N/2-1][i+M/2-1] = setColorDensity(val, 1);
				tpixels[N/2-j][M/2-i] = setColorDensity(val, 1);
			}
			if ( i >= M/2 && j <= N/2) {
				tpixels[j+N/2-1][i-M/2] = setColorDensity(val, 1);
				tpixels[N/2-j][M+M/2-i-1] = setColorDensity(val, 1);
			} 
          }
	}
	
	fftw2d_free(a);
}
/* }}} */

/* {{{	vim options
 * Local variables:
 * c-basic-offset: 4
 * End:
 * vim600: noet sw=4 ts=4 fdm=marker
 * vim<600: noet sw=4 ts=4
}}} */
