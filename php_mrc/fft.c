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
#include "filter.h"
#include "php_mrc.h"
#include "fft.h"
#include <sfftw.h>
#include <srfftw.h>



double square(fftw_complex C) {
		return log(sqrt(C.re * C.re + C.im * C.im));
}

void getfft(gdImagePtr im_src) {
  int i,j;
  if (im_src->tpixels)
      for (i = 0; (i < im_src->sy); i++)
	      for (j = 0; (j < im_src->sx); j++)
          		im_src->tpixels[i][j] = im_src->tpixels[i][j];
	getFFT(im_src->sx, im_src->sy, im_src->tpixels);
}

/*
Standard deviation
moyenne m = Sx / n

deviation: x - m

somme des D = (x - m)^2

stddev = sqrt(D / n)


*/

double fftw_info(MRC *pMRC, Info *pInfo, int mask_radius) {



	int densitymax = 255;
	int i,j,ij;

	int M = pMRC->header.nx;
	int N = pMRC->header.ny;
	int mode=pMRC->header.mode;

	double	minval = pMRC->header.amin,
		maxval = pMRC->header.amax,
		scale = maxval - minval,
		val,
		nminval, nmaxval;

	double somme=0, avg=0, variance=0, n=0, stddev=0;


	rfftwnd_plan plan;
	fftw_real a[M][2*(N/2+1)], b[M][2*(N/2+1)];
	fftw_complex *A;
	fftw_real *data_array;

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
	 case MRC_MODE_FLOAT:
         {
		data_array = (fftw_real *)((float *)pMRC->pbyData);
		break;
         }
	}
	for (i = 0; i < M; ++i) {
		for (j = 0; j < N; ++j) {
			ij = i*N + j;
			a[i][j] = (fftw_real)(data_array[ij]);
		}
	}


	plan = rfftw2d_create_plan(M, N, FFTW_REAL_TO_COMPLEX, FFTW_ESTIMATE | FFTW_IN_PLACE);
	rfftwnd_one_real_to_complex(plan, &a[0][0], NULL);
	rfftwnd_destroy_plan(plan);

	minval = maxval = square(A[0]);
	for (i = 0; i < M; ++i) {
          for (j = 0; j < N/2+1; ++j) {
		ij = i*(N/2+1) + j;

		// --- mask DC component of FFT with a given radius
		if (mask_radius > 0 && (
					(sqrt(i*i + j*j) < mask_radius) || 
					(sqrt((N-i)*(N-i) + j*j) < mask_radius) )) {
			data_array[ij] = 0;
			continue;
		}

		val = square(A[ij]);
		if (val>0) {
			somme += val;
			n++;
			data_array[ij] = val;
			maxval = MAX(maxval, val);
			minval = MIN(minval, val);
		}
	  }
	}

	scale = maxval - minval;
	avg = somme/n;

	for (ij=0; ij < n; ij++) {
		val = data_array[ij];
		variance += (val-avg)*(val-avg);
	}

	stddev = sqrt(variance/n);
	nmaxval = avg + 3 * stddev; 
	nminval = avg - 3 * stddev; 

	scale = nmaxval - nminval;


	pInfo->minval = minval;
	pInfo->maxval = maxval;
	pInfo->nminval = nminval;
	pInfo->nmaxval = nmaxval;
	pInfo->avg = avg;
	pInfo->stddev = stddev;
	pInfo->scale = scale;
	pInfo->n = n;

	return 1;

}

int mrc_to_fftw_image(MRC *pMRC, int ** tpixels, int mask_radius, int minpix, int maxpix, int colormap) {

	int i,j,ij;

	int M = pMRC->header.nx;
	int N = pMRC->header.ny;
	int mode=pMRC->header.mode;
	int densitymax = (colormap) ? densityColorMAX : densityMAX;
	int gray = (colormap) ? 0 : 1;

	double	minval = pMRC->header.amin,
		maxval = pMRC->header.amax,
		scale = maxval - minval,
		val,
		nminval, nmaxval;

	double somme=0, avg=0, variance=0, n=0, stddev;

	rfftwnd_plan plan;
	fftw_real a[M][2*(N/2+1)], b[M][2*(N/2+1)];
	fftw_complex *A;
	fftw_real *data_array;

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
	 case MRC_MODE_FLOAT:
         {
		data_array = (fftw_real *)((float *)pMRC->pbyData);
		break;
         }
	}
	for (i = 0; i < M; ++i) {
		for (j = 0; j < N; ++j) {
			ij = i*N + j;
			a[i][j] = (fftw_real)(data_array[ij]);
		}
	}

	plan = rfftw2d_create_plan(M, N, FFTW_REAL_TO_COMPLEX, FFTW_ESTIMATE | FFTW_IN_PLACE);
	rfftwnd_one_real_to_complex(plan, &a[0][0], NULL);
	rfftwnd_destroy_plan(plan);

	minval = maxval = square(A[0]);
	for (i = 0; i < M; ++i) {
          for (j = 0; j < N/2+1; ++j) {
		ij = i*(N/2+1) + j;

		// --- mask DC component of FFT with a given radius
		if (mask_radius > 0 && (
					(sqrt(i*i + j*j) < mask_radius) || 
					(sqrt((N-i)*(N-i) + j*j) < mask_radius) )) {
			data_array[ij] = 0;
			continue;
		}
		val = square(A[ij]);
			
		if (val>0) {
			somme += val;
			n++;
			data_array[ij] = val;
			maxval = MAX(maxval, val);
			minval = MIN(minval, val);
		}
	  }
	}

	scale = maxval - minval;
	if (n>0)
		avg = somme/n;

	for (ij=0; ij < n; ij++) {
		val = data_array[ij];
		variance += (val-avg)*(val-avg);
	}

	if (n>0)
		stddev = sqrt(variance/n);
	nmaxval = avg + 3 * stddev ; 
	nminval = avg - 3 * stddev; 
	scale = nmaxval - nminval;

	nminval = minpix*scale/densitymax + nminval;
	nmaxval = maxpix*scale/densitymax + nminval;
	if (minpix > maxpix)
		scale *= -1;

	for (i = 0; i < M; ++i) {
          for (j = 0; j < N/2+1; ++j) {
		ij = i*(N/2+1) + j;
		val = data_array[ij];
		val = val*densitymax/scale - nminval*densitymax/scale; 
		if (i <= M/2 && j <= N/2) {
			tpixels[i+M/2-1][j+N/2-1] = setColorDensity(val, gray);
			tpixels[M/2-i][N/2-j] = setColorDensity(val, gray);
		}

		if ( i >= M/2 && j <= N/2) {
			tpixels[i-M/2][j+N/2-1] = setColorDensity(val, gray);
			tpixels[M+M/2-i-1][N/2-j] = tpixels[i-M/2][j+N/2-1];
		} 
          }
	}
}

void getFFT(int M, int N, int ** tpixels ) {
	double f_val,
		scale,
		min, max,
		fmin, fmax;
	int densitymax = densityMAX;
	int gray =  1;
	int i, j;

	rfftwnd_plan plan;
	fftw_real a[M][2*(N/2+1)];
	fftw_complex *A;

	A = (fftw_complex*) &a[0][0];

	for (i = 0; i < M; ++i)
          for (j = 0; j < N; ++j) {
             a[i][j] = (fftw_real)getDensity(tpixels[i][j]);
          }

	plan = rfftw2d_create_plan(M, N, FFTW_REAL_TO_COMPLEX, FFTW_ESTIMATE | FFTW_IN_PLACE);
	rfftwnd_one_real_to_complex(plan, &a[0][0], NULL);
	rfftwnd_destroy_plan(plan);

	fmax = fmin = 0;
	for (i = 0; i < M; ++i) {
          for (j = 0; j < N/2+1; ++j) {
		int ij = i*(N/2+1) + j;
		f_val = sqrt(((A[ij].re * A[ij].re + A[ij].im * A[ij].im)));
		if (f_val>0) {
			f_val = log(f_val);
			fmax = MAX(fmax, f_val);
			fmin = MIN(fmin, f_val);
		}
	  }
	}
	scale = fmax - fmin;
		

	for (i = 0; i < M; ++i) {
          for (j = 0; j < N/2+1; ++j) {
		int ij = i*(N/2+1) + j;
		f_val = (((A[ij].re * A[ij].re + A[ij].im * A[ij].im)));
		if (f_val>0) {
			f_val = log(f_val);
			f_val = f_val/scale*densitymax;
			if (i <= M/2 && j <= N/2) {
				tpixels[i+M/2-1][j+N/2-1] = setColorDensity(f_val, 1);
				tpixels[M/2-i][N/2-j] = setColorDensity(f_val, 1);
			}
			if ( i >= M/2 && j <= N/2) {
				tpixels[i-M/2][j+N/2-1] = setColorDensity(f_val, 1);
				tpixels[M+M/2-i-1][N/2-j] = tpixels[i-M/2][j+N/2-1];
			} 
		}
          }
	}
}

