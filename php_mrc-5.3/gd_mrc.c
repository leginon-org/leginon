#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "php.h"
#include "gd_unbundled.h"
#include "gd.h"
#include "mrc.h"
#include "gd_mrc.h"
#include "filter.h"

/**
 * void mrc_to_float(MRC *mrc, float *pdata_array)
 */
void mrc_to_float(MRC *mrc, float *pdata_array) {

        int     h=mrc->header.nx, w=mrc->header.ny,
                mode=mrc->header.mode;

				long		n=w*h,
                i;

        switch (mode) {
         case MRC_MODE_BYTE:
         {
                char *data_array_char = (char *)mrc->pbyData;
                for (i = 0; i < n; ++i) {
                        pdata_array[i] = (float)data_array_char[i];
                }

         }
         break;
         case MRC_MODE_SHORT:
         {
                short *data_array_short = (short *)mrc->pbyData;
                for (i = 0; i < n; ++i) {
                        pdata_array[i] = (float)data_array_short[i];
                }

         }
         break;
         case MRC_MODE_FLOAT:
         {
                memcpy(pdata_array, (float *)mrc->pbyData, sizeof(float)*n);

         }
         break;
         case MRC_MODE_UNSIGNED_SHORT:
         {
                unsigned short *data_array_ushort = (unsigned short *)mrc->pbyData;
                for (i = 0; i < n; ++i) {
                        pdata_array[i] = (float)data_array_ushort[i];
                }
         }
         break;
        }
}


/**
 * void mrc_convert_to_float(MRC *mrc_src, MRC *mrc_dst)
 */
void mrc_convert_to_float(MRC *mrc_src, MRC *mrc_dst) {

	float	*data_array, *data_array_dst;

  int		w_src=mrc_src->header.nx, h_src=mrc_src->header.ny;

	long	n_src=w_src*h_src;

	memcpy(&mrc_dst->header, &mrc_src->header, MRC_HEADER_SIZE);

	mrc_dst->header.nx = w_src;
	mrc_dst->header.ny = h_src;
	mrc_dst->header.mode = MRC_MODE_FLOAT;

	mrc_dst->pbyData = malloc(sizeof(float)*n_src);
	data_array_dst = (float *)mrc_dst->pbyData;
	
	mrc_to_float(mrc_src, data_array_dst);

}


/**
 * MRCPtr mrc_create(int x_size, int y_size)
 *
 * set mode as FLOAT by default
 */
MRCPtr mrc_create(int x_size, int y_size) {

	long n = x_size * y_size;
	char map[4] = "MAP ";
	char *pmap;
	MRCPtr pmrc;

	pmrc = (MRC *) malloc (sizeof (MRC));
	memset (pmrc, 0, sizeof (MRC));
	pmrc->header.nx = x_size;
	pmrc->header.ny = y_size;
	pmrc->header.nz = 1;
	pmrc->header.mode = MRC_MODE_FLOAT;
	pmap = pmrc->header.map;
	memcpy(pmap, map, 4);
	pmrc->pbyData = malloc(sizeof(float)*n);
	memset (pmrc->pbyData, 0, sizeof(float)*n);

	return pmrc;

}


/**
 * void mrc_update_header(MRC *mrc)
 */
void mrc_update_header(MRC *mrc) {

	int	i=0;
	double	somme=0, somme2=0, n=0; 

	float   fmin,
			fmax,
			fmean,
			stddev,
			f_val;

	float *data_array;

	data_array = (float *)mrc->pbyData;
	n = mrc->header.nx * mrc->header.ny;

	fmax = fmin = data_array[0];
	for (i = 0; i < n; i++) {
		f_val = data_array[i];
		fmax = MAX(fmax, f_val);
		fmin = MIN(fmin, f_val);
		somme  += f_val;
		somme2 += f_val*f_val;
	}

	if (n>0) {
		fmean = somme/n;
		stddev = sqrt((somme2 * n - somme * somme) / (n*n));
	}

	mrc->header.amin = fmin;
	mrc->header.amax = fmax;
	mrc->header.amean = fmean;
	mrc->header.rms = stddev;

}


/**
 * void mrc_filter(MRC *mrc, int binning, int kernel, float sigma)
 */
void mrc_filter(MRC *mrc, int binning, int kernel, float sigma) {

	float *data_array_src ;
	float f_val;

	long index, ij, IJ;

	int	i, j,
		n_w, w, n_h, h;

	int	*maskindexes;
	int	maskindex=0,
		masksize = kernel*kernel;


	double  *maskData;

	if (binning>0 && sigma !=0 && kernel % 2 == 1) {

		w = mrc->header.nx;
		h = mrc->header.ny;
		n_w = w/binning;
		n_h = h/binning;

		data_array_src = (float *)mrc->pbyData;
		maskData = malloc(sizeof(double)*masksize);
		maskindexes = malloc(sizeof(int)*masksize);

		gaussianfiltermask(maskData, kernel, sigma);

		for (j=0; j<n_h; j++) {
			for (i=0; i<n_w; i++) {
				ij = i + j*n_w;
				IJ = i*binning + j*w*binning;
				getMaskDataIndexes(maskindexes, kernel, IJ, w);
				for (f_val=0, index = 0; index < masksize; index++) {
					if (maskindexes[index] != -1)
						f_val += data_array_src[maskindexes[index]] * maskData[index];
				}
				data_array_src[ij] = f_val;
			}
		}

		mrc->header.nx=n_w;
		mrc->header.ny=n_h;
		free(maskData);
		free(maskindexes);
	}

}


/**
 * void mrc_binning(MRC *mrc, int binning, int skip_avg)
 */
void mrc_binning(MRC *mrc, int binning, int skip_avg) {

	float *data_array_src ;
	float f_val;

	long	ij, IJ;

	int *indexes;
	int	i, j,
		n_w, w,
		n_h, h,
		binningsize,
		index;

	if (binning>1) {
		
 		binningsize = binning*binning;
		indexes = malloc(sizeof(int)*binningsize);
		data_array_src = (float *)mrc->pbyData;
		w = mrc->header.nx;
		h = mrc->header.ny;
		n_w = w/binning;
		n_h = h/binning;

		for (j=0; j<n_h; j++) {
			for (i=0; i<n_w; i++) {
				ij = i + j*n_w;
				IJ = i*binning + j*w*binning;
				if (skip_avg) {
					f_val = data_array_src[IJ];
				} else {
					getIndexes(indexes, binning, IJ, w);
					for (f_val=0, index=0; index<binningsize; index++)
						f_val += data_array_src[indexes[index]];
					f_val /= binningsize;
				}
				data_array_src[ij] = f_val;
			}
		}
		mrc->header.nx=n_w;
		mrc->header.ny=n_h;
		free(indexes);
	}
}


/**
 * void mrc_log(MRC *mrc)
 */
void mrc_log(MRC *mrc) {

	float *data_array_src ;
	float val;

	long	n;

	int	w, h, i;

	w = mrc->header.nx;
	h = mrc->header.ny;
	n=w*h;

	data_array_src = (float *)mrc->pbyData;
	for (i = 0; i < n; ++i) {
		val = data_array_src[i];
		if (val!=0)
		data_array_src[i] = log(val);
	}

	mrc_update_header(mrc);
}


/**
 * void mrc_to_gd(MRC *mrc, int ** tpixels, int pmin, int pmax) {
 */
void mrc_to_gd(MRC *mrc, gdImagePtr im, int pmin, int pmax) {

	float	*data_array;
	float   fmin=mrc->header.amin,
			fmax=mrc->header.amax,
			scale = fmax - fmin,
			nmin, nmax,
			nscale,
			f_val;

	int	w=mrc->header.nx, h=mrc->header.ny,
		i,j;
	int densitymax = DENSITY_MAX;

	long n=w*h, ij;


	data_array = (float *)mrc->pbyData;

	nmin = fmin + pmin * scale / densitymax;
	nmax = fmin + pmax * scale / densitymax;
	nscale = nmax - nmin;

	if (nscale != 0)
		for (j = 0; j < h; ++j) {
			for (i = 0; i < w; ++i) {
				ij = i + j*w;
				f_val = data_array[ij];
				f_val = (f_val-nmin)*densitymax/nscale;
				gdImageSetPixel (im, i, j, setDensity(f_val));
			}
		}

}


/**
 * void mrc_copy(MRCPtr pmrc_dst, MRCPtr pmrc_src, int x1, int y1, int x2, int y2)
 */
void mrc_copy(MRCPtr pmrc_dst, MRCPtr pmrc_src, int x1, int y1, int x2, int y2) {

	float	*data_array_src, *data_array_dst;

	int	w_src=pmrc_src->header.nx, h_src=pmrc_src->header.ny,
			w_dst, h_dst, 
			x_min=x1, x_max=x2,
			y_min=y1, y_max=y2;

	if (x1>x2) {
		x_min=x2;
		x_max=x1;
	}
	if (y1>y2) {
		y_min=y2;
		y_max=y1;
	}
	if (x_max > w_src)
		x_max = w_src;
	if (y_max > h_src)
		y_max = h_src;

	mrc_copy_to(pmrc_dst, pmrc_src, 0, 0, x_min, y_min, x_max, y_max);

}


/**
 * void mrc_copy_to(MRCPtr pmrc_dst, MRCPtr pmrc_src, int dstX, int dstY, int srcX, int srcY, int w, int h)
 * mrc_copy_to(mrc_dst, mrc_src, dstX, dstY, srcX, srcY, srcW, srcH);
 */

void mrc_copy_to(MRCPtr pmrc_dst, MRCPtr pmrc_src, int dstX, int dstY, int srcX, int srcY, int srcW, int srcH)
{
	int	w,h,w_src, h_src,
			w_dst, h_dst; 

	long	n_src, n_dst,
				i,j,ij,u,v,uv;

	float	*data_array_src, *data_array_dst;

	w_src = pmrc_src->header.nx;
	h_src = pmrc_src->header.ny;
	n_src = w_src * h_src;
	w_dst = pmrc_dst->header.nx;
	h_dst = pmrc_dst->header.ny;
	n_dst = w_dst * h_dst;
	srcX = (srcX>w_src) ? w_src : srcX;
	srcY = (srcY>h_src) ? h_src : srcY;
	w = (srcW>w_src) ? w_src : srcW;
	h = (srcH>h_src) ? h_src : srcH;

	if (srcX<0) {
		w+=srcX;
		srcX=0;
	}
	if (srcY<0) {
		h+=srcY;
		srcY=0;
	}

	data_array_dst = (float *)pmrc_dst->pbyData;
	data_array_src = (float *)pmrc_src->pbyData;

	for (v=dstY, j=srcY; j<srcY+h_dst; j++, v++) {
		for (u=dstX, i=srcX; i<w; i++, u++) {
			ij = i + j*w_src;
			uv = u + v*w_dst;
			if ((u>=w_dst) || (v>=h_dst) ||
					(u<0) || (v<0) ||
					(ij<0) || (uv<0) ||
					(ij>n_src-1) || (uv>n_dst-1)
				)
				continue;
			data_array_dst[uv] = data_array_src[ij];
		}
	}
	
}


/**
 * int mrc_copy_from_file(MRCPtr pmrc_dst, char *pszFilename, int dstX, int dstY, int srcX, int srcY, int srcW, int srcH)
 */
int mrc_copy_from_file(MRCPtr pmrc_dst, char *pszFilename, int dstX, int dstY, int srcX, int srcY)
{
	FILE *pFMRC;
	MRCHeader pmrch;

	unsigned int uElementSize = 0;

	int w, h,
			w_src, h_src,
			w_dst, h_dst,
			offset; 

	long	n_src, n_dst,
				i,j,ij,u,v,uv;


	float *data_array = (float *)pmrc_dst->pbyData;

	if((pFMRC = fopen(pszFilename, "rb")) == NULL)
		return -1;

	if(!readMRCHeader(pFMRC, &pmrch)) {
		return -2;
	}

	w_src = pmrch.nx;
	h_src = pmrch.ny;
	n_src = w_src * h_src;
	w_dst = pmrc_dst->header.nx;
	h_dst = pmrc_dst->header.ny;
	n_dst = w_dst * h_dst;
	srcX = (srcX>w_src) ? w_src : srcX;
	srcY = (srcY>h_src) ? h_src : srcY;

	// set new header
	pmrc_dst->header.amin=pmrch.amin;
	pmrc_dst->header.amax=pmrch.amax;
	pmrc_dst->header.amean=pmrch.amean;
	pmrc_dst->header.rms=pmrch.rms;

	w = (w_dst>w_src) ? w_src : w_dst+srcX;
	h = h_dst+srcY;
	offset = (w_dst>w_src) ? 
						(dstX<0) ? srcX-dstX : srcX 
						: w_src-w_dst+abs(dstX);

	if(pmrch.mode == MRC_MODE_BYTE) 
		{
			uElementSize = sizeof(char);
			char data_val[1];
			// --- position pointer file where copy should start: (srcX, srcY);
			fseek(pFMRC, (srcX+srcY*w_src)*uElementSize, SEEK_CUR);
			for (v=dstY, j=srcY; j<h; j++, v++) {
				for (u=dstX, i=srcX; i<w; i++, u++) {
					ij = i + j*w_src;
					uv = u + v*w_dst;
					if ((u>=w_dst) || (v>=h_dst) ||
							(u<0) || (v<0) ||
							(ij<0) || (uv<0) ||
							(ij>n_src-1) || (uv>n_dst-1)
						)
							continue;
					fread(data_val, uElementSize,1,pFMRC);
					data_array[uv] = *data_val;
				}
				// --- seek next row of interested area
				fseek(pFMRC, offset*uElementSize, SEEK_CUR);
			}
		} else if (pmrch.mode==MRC_MODE_SHORT)
		{
			uElementSize = sizeof(short);
			short data_val[1];
			// --- position pointer file where copy should start: (srcX, srcY);
			fseek(pFMRC, (srcX+srcY*w_src)*uElementSize, SEEK_CUR);
			for (v=dstY, j=srcY; j<h; j++, v++) {
				for (u=dstX, i=srcX; i<w; i++, u++) {
					ij = i + j*w_src;
					uv = u + v*w_dst;
					if ((u>=w_dst) || (v>=h_dst) ||
							(u<0) || (v<0) ||
							(ij<0) || (uv<0) ||
							(ij>n_src-1) || (uv>n_dst-1)
						)
							continue;
					fread(data_val, uElementSize,1,pFMRC);
					data_array[uv] = *data_val;
				}
				// --- seek next row of interested area
				fseek(pFMRC, offset*uElementSize, SEEK_CUR);
			}

		} else if (pmrch.mode == MRC_MODE_UNSIGNED_SHORT) 
		{
			uElementSize = sizeof(unsigned short);
			unsigned short data_val[1];
			// --- position pointer file where copy should start: (srcX, srcY);
			fseek(pFMRC, (srcX+srcY*w_src)*uElementSize, SEEK_CUR);
			for (v=dstY, j=srcY; j<h; j++, v++) {
				for (u=dstX, i=srcX; i<w; i++, u++) {
					ij = i + j*w_src;
					uv = u + v*w_dst;
					if ((u>=w_dst) || (v>=h_dst) ||
							(u<0) || (v<0) ||
							(ij<0) || (uv<0) ||
							(ij>n_src-1) || (uv>n_dst-1)
						)
							continue;
					fread(data_val, uElementSize,1,pFMRC);
					data_array[uv] = *data_val;
				}
				// --- seek next row of interested area
				fseek(pFMRC, offset*uElementSize, SEEK_CUR);
			}

		} else if (pmrch.mode = MRC_MODE_FLOAT) 
		{
			uElementSize = sizeof(float);
			// --- position pointer file where copy should start: (srcX, srcY);
			fseek(pFMRC, (srcX+srcY*w_src)*uElementSize, SEEK_CUR);
			for (v=dstY, j=srcY; j<h; j++, v++) {
				for (u=dstX, i=srcX; i<w; i++, u++) {
					ij = i + j*w_src;
					uv = u + v*w_dst;
					if ((u>=w_dst) || (v>=h_dst) ||
							(u<0) || (v<0) ||
							(ij<0) || (uv<0) ||
							(ij>n_src-1) || (uv>n_dst-1)
						)
							continue;
					fread(&(data_array[uv]), uElementSize,1,pFMRC);
				}
				// --- seek next row of interested area
				fseek(pFMRC, offset*uElementSize, SEEK_CUR);
			}
		}
	
	fclose(pFMRC);
	return 1;
}


/**
 * void mrc_normalize(MRCPtr pmrc_raw, MRCPtr pmrc_norm, MRCPtr pmrc_dark)
 */
void mrc_normalize(MRCPtr pmrc_raw, MRCPtr pmrc_norm, MRCPtr pmrc_dark)
{
	int w_raw, h_raw, n_raw,
			w_norm, h_norm, n_norm,
			i;
	float diff;

	float	*data_array_raw, *data_array_norm, *data_array_dark;

	w_raw = pmrc_raw->header.nx;
	h_raw = pmrc_raw->header.ny;
	n_raw = w_raw * h_raw;

	data_array_raw = (float *)pmrc_raw->pbyData;
	data_array_norm = (float *)pmrc_norm->pbyData;
	data_array_dark = (float *)pmrc_dark->pbyData;

	for (i=0; i<n_raw; i++) {
			diff = data_array_raw[i] - data_array_dark[i];
			data_array_raw[i] = diff * data_array_norm[i];
	}
	
}


/**
 * void mrc_destroy(MRCPtr pmrc)
 */
void mrc_destroy(MRCPtr pmrc) {
	free(pmrc->pbyData);
	free(pmrc);
}


/**
 * void mrc_to_histogram(MRC *mrc, int *frequency, float *classes, int nb_bars)
 */
void mrc_to_histogram(MRC *mrc, int *frequency, float *classes, int nb_bars) {
        float   fmin=mrc->header.amin,
                fmax=mrc->header.amax,
                interval;
        float *data_array;

        int     h=mrc->header.nx, w=mrc->header.ny;
        int i, i1, i2, j, d;
        int mode=mrc->header.mode;
        int nb=0;
				long	n=w*h;

        interval=(fmax-fmin)/nb_bars;

		data_array = (float *)mrc->pbyData;

        if(interval <= 0) {
                fmax = fmin = (float)data_array[0];
                for (i = 0; i<n ; i++) {
                        fmax = MAX(fmax, data_array[i]);
                        fmin = MIN(fmin, data_array[i]);
                }
                interval=(fmax-fmin)/nb_bars;
        }
        for (i=0; i<nb_bars; i++) {
                nb=0;
                for (d=0; d<n; d++) {
                        i1 = fmin+(i-1)*interval;
                        i2 = fmin+i*interval;
                        if (data_array[d] > i1 && data_array[d] <=i2)
                                nb++;
                }
                classes[i] = fmin + i*interval;
                frequency[i] = nb;
        }
}

void mrc_to_frequence(MRC *mrc, int *frequency) {
	float fmin=mrc->header.amin,
			  fmax=mrc->header.amax;
	float	*data_array;
	int h=mrc->header.nx, w=mrc->header.ny;
	int i, i1, i2, j, d;
	int mode=mrc->header.mode;
	int nb=0;
	int i_val, interval;
	long	n=w*h;


	data_array = (float *)mrc->pbyData;

	interval=(int)(fmax-fmin);
	if(interval <= 0) {
		fmax = fmin = (float)data_array[0];
		for (i = 0; i<n ; i++) {
			fmax = MAX(fmax, data_array[i]);
			fmin = MIN(fmin, data_array[i]);
		}
		interval=(int)(fmax-fmin);
	}
	for (i = 0; i < n; i++) {
		i_val = (int)(data_array[i]-fmin);
		frequency[i_val] += 1;
	}
}


/**
 * int getIndexes(int *indexes, int binning, int index, int imagewidth)
 *
 * get pixel indexes from a  binning factor applied to a pixel index
 */
int getIndexes(int *indexes, int binning, int index, int imagewidth) {
	int	i=0,
		b_w=0,
		b_h=0;

	for(b_w=0; b_w<binning; b_w++)
                for(b_h=0; b_h<binning; b_h++, i++)
                        indexes[i] = index + b_w*imagewidth + b_h;
}


/**
 * int getMaskDataIndexes(int *indexes, int kernel, int index, int imagewidth)
 *
 * get pixel indexes from a mask (kernelxkernel) applied to a pixel index
 */
int getMaskDataIndexes(int *indexes, int kernel, int index, int imagewidth) {
	int	i=0,
		m_w=0,
		m_h=0,
		max_size = imagewidth*imagewidth,
		max_index,
		ni,
		index_row = index/imagewidth;

	for(m_w=0; m_w<kernel; m_w++) {
                for(m_h=0; m_h<kernel; m_h++, i++) {
                        indexes[i] = index + m_w*imagewidth + m_h;
                        ni = index + m_w * imagewidth + m_h;
                        max_index  = imagewidth * (index_row + m_w + 1);
                        if (ni >= max_index  || max_index  > max_size )
                                ni = -1;
                        indexes[i] = ni;
                }
        }
}


/**
 * int gdreadMRCHeader(gdIOCtx *io_ctx, MRCHeader *pMRCHeader)
 */
int gdreadMRCHeader(gdIOCtx *io_ctx, MRCHeader *pMRCHeader) {

	gdGetBuf(pMRCHeader, MRC_HEADER_SIZE, io_ctx);
	if(	(pMRCHeader->nx < 0) || (pMRCHeader->ny < 0) || 
		(pMRCHeader->nz < 0) || (pMRCHeader->mode < 0) || 
		(pMRCHeader->mode > 4) || (pMRCHeader->x_length < 0) ||
		(pMRCHeader->y_length < 0) || (pMRCHeader->z_length < 0) ||
		(pMRCHeader->x_length > pMRCHeader->nx ) ||
		(pMRCHeader->y_length > pMRCHeader->ny ) ||
		(pMRCHeader->z_length > pMRCHeader->nz ) 
	)
			return -1; /* This is not a valid pMRCHeader header */
	return 1 ;
}


/**
 * int gdloadMRC(gdIOCtx *io_ctx, int in_length, MRC *pMRC)
 */
int gdloadMRC(gdIOCtx *io_ctx, int in_length, MRC *pMRC) {
	unsigned int uElementSize = 0;
	unsigned int uElements = 0;

	if (gdreadMRCHeader(io_ctx, &(pMRC->header))==-1)
		return -1;

	uElements = pMRC->header.nx * pMRC->header.ny * pMRC->header.nz;

	switch(pMRC->header.mode) {
		case MRC_MODE_BYTE:
			uElementSize = sizeof(char);
			break;
		case MRC_MODE_SHORT:
			uElementSize = sizeof(short);
			break;
		case MRC_MODE_UNSIGNED_SHORT:
			uElementSize = sizeof(short);
			break;
		case MRC_MODE_FLOAT:
			uElementSize = sizeof(float);
			break;
		case MRC_MODE_SHORT_COMPLEX:
			uElementSize = sizeof(short);
			uElements *= 2;
			break;
		case MRC_MODE_FLOAT_COMPLEX:
			uElementSize = sizeof(float);
			uElements *= 2;
			break;
		default:
			return -1;
	}
	if (in_length != (uElements*uElementSize+MRC_HEADER_SIZE))
		return -1;
	

	if((pMRC->pbyData = malloc(uElements*uElementSize)) == NULL)
		pMRC->pbyData = malloc(uElements*uElementSize);

	if(!gdGetBuf(pMRC->pbyData, (uElements*uElementSize), io_ctx))
	return -1;
	
	return 1;
}

/**
 * void mrc_rotate(MRC *mrc, double angle, int resize)
 */

MRCPtr mrc_rotate(MRC *mrc_src, double angle, int resize) {

	MRCPtr mrc_dst;

	float	*data_array_src, *data_array_dst;

	float min_val=mrc_src->header.amin;

	int	w_src=mrc_src->header.nx, h_src=mrc_src->header.ny;
	int	w_dst, h_dst;

	long n_src=w_src*h_src;

	if (resize) {
					cal_rotated_image_dimension(h_src, w_src, angle, &h_dst, &w_dst);
	} else {
		w_dst=w_src;
		h_dst=h_src;
	}
	mrc_dst = mrc_create(w_dst, h_dst);
	data_array_src = (float *)mrc_src->pbyData;
	data_array_dst = (float *)mrc_dst->pbyData;
	rotate_2d_image (data_array_src, data_array_dst, h_src, w_src, angle, h_dst, w_dst, min_val);
	return mrc_dst;
}

/**
 * float * rotate_2d_image (float *in_img, int h, int w, double ang, int new_h, int new_w, 
 *                          float default_value)
 *
 * Description   : rotate image in_img about its center by angle ang (in radians).
 *                 To solve the problem, we need to consider the problem backwards. 
 *                 For each pixel(x',y') in the output image, use the inverse of the 
 *                 rotation functions to figure out which input-image pixel (x,y) maps to it.
 *                 Then bilinear interpolation is used to generate pixel value.
 *                 Following equation relates pixel(x',y') to pixel(x,y)
 *
 *                     | x'|   | cos(theta) -sin(theta) |   | x - x_c |     | x_c' |
 *                     |   | = |                        | * |         |   + |      |
 *                     | y'|   | sin(theta)  cos(theta) |   | y - y_c |     | y_c' |
 *
 *                     and,
 *
 *                     | x |   | cos(theta)  sin(theta) |   | x' - x_c' |   | x_c |
 *                     |   | = |                        | * |           | + |     |
 *                     | y |   | -sin(theta) cos(theta) |   | y' - y_c' |   | y_c |
 *
 *
 *                 where (x_c, y_c) and (x'_c, y'_c) are centers of the image before and after
 *                 rotation, respectively.
 *
 * Return type      : rotated image.
 *
 * Argument         : in_img -- input image.
 * Argument         : h -- height of the input image.
 * Argument         : w -- width of the input image.
 * Argument         : new_h -- height of the rotated image.
 * Argument         : new_w -- width of the rotated image.
 *
 *
 */
int rotate_2d_image (float *in_img, float *out_img, int h, int w, double ang, int new_h, int new_w, 
                          float default_value)
{
    int old_xmid, old_ymid, new_xmid, new_ymid, new_x, new_y, index;
   float  dx, dy, old_x, old_y;
   double  sine, cosine;

   sine = sin(ang);
   cosine = cos(ang);
   old_xmid = (int) floor(w/2.0 + 0.5);
   old_ymid = (int) floor(h/2.0 + 0.5);
   new_xmid = (int) floor(new_w/2.0 + 0.5);
   new_ymid = (int) floor(new_h/2.0 + 0.5);

   for (index=0, new_y=0; new_y<new_h; new_y++) /* visit each row in in_img.*/
       for (new_x=0; new_x<new_w; new_x++, index++ ) {
          /* visit each pixel within the xth row. */
          dx = new_x - new_xmid;
          dy = new_y - new_ymid;
          old_x = cosine * dx + sine * dy + old_xmid;
          old_y = cosine * dy - sine * dx + old_ymid;
          out_img[index] = linear_2d_interp (in_img, h, w, old_x, old_y, default_value);
       }
   return 1;
}

/*
 * Function name :  linear_2d_interp
 *
 * Return type      : intensity value of the interploted pixel.
 *
 * Argument         : in_img -- input image.
 * Argument         : h -- height of the input image.
 * Argument         : w -- width of the input image.
 * Argument         : old_x, old_y -- intended location of the pixel.
 *
 */
float linear_2d_interp (float *in_img, int h, int w, float old_x, float old_y, float default_value)
 {
   int floor_x, floor_y, ceil_x, ceil_y, offset1, offset2;
   float rem_x, rem_y;
   float out_value;

   if (old_x < 0. || old_x > w-1.0 || old_y < 0. || old_y > h - 1.0)
       out_value = default_value;
   else{
        floor_y = ((int) floor(old_y)) % h;
        ceil_y = ((int) ceil(old_y)) % h;
        rem_y = old_y - ((float) floor_y);

        floor_x = ((int) floor(old_x)) % w;
        ceil_x = ((int) ceil(old_x)) % w;
        rem_x = old_x - ((float) floor_x);

        offset1 = floor_y * w;
        offset2 = ceil_y * w;
        out_value = linear_interp(linear_interp(in_img[offset1+floor_x],
                    in_img[offset2+floor_x], rem_y), linear_interp(in_img[offset1+ceil_x],
                    in_img[offset2+ceil_x], rem_y), rem_x);
   }
   return out_value;
}

/**
 * float linear_interp(float low_value, float high_value, float position)
 */
float linear_interp(float low_value, float high_value, float position)
{
  float result;
  result = low_value * (1.0 - position) + high_value * position;
  return(result);
}

/**
 * void cal_rotated_image_dimension(int h, int w, double ang, int *new_h, int *new_w)
 */
void cal_rotated_image_dimension(int h, int w, double ang, int *new_h, int *new_w)
{
   double sine, cosine;

   sine = sin(ang);
   cosine = cos(ang);
   *new_w = (int)(h * fabs(sine) + w * fabs(cosine)) ;  /* final image width */
   *new_h = (int)(w * fabs(sine) + h * fabs(cosine)) ;  /* final image height */

}


/**
 * vim command
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * End:
 * vim600: noet sw=4 ts=4 fdm=marker
 * vim<600: noet sw=4 ts=4
 }}}
 */
