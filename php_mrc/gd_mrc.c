#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "php.h"
#include "gd.h"
#include "mrc.h"
#include "gd_mrc.h"
#include "filter.h"

/*
convert mrc data into an image resource pixels array.
The following parameters can be set:
	- binning (skip=1 -> neighbour pixel won't be averaged
	- pixel value rescaling (pmin <= pixel value  => pmax)
	- gaussian filter (kernel size, sigma)
*/
void mrc_to_image(MRC *mrc, int ** tpixels,
			int pmin, int pmax,
			int binning, int skip,
			int kernel, float sigma, int colormap)
{

	float	fmin=mrc->header.amin,
		fmax=mrc->header.amax,
		scale = fmax - fmin,
		min, max,
		f_val;

	int	h=mrc->header.nx, w=mrc->header.ny,
		n=w*h,
		mode=mrc->header.mode,
		i,j,t,
		index,
		binningsize = binning*binning,
		indexes[binningsize],
		n_w = w/binning,
		n_h = w/binning,
		off_w = w - n_w * binning;

	int	filter = 0,
		maskindex=0,
		masksize = kernel*kernel,
		maskindexes[masksize],
		x=0,
		y=0;

	double	maskData[masksize];

	float	density,
		ndensity;

	int densitymax = (colormap) ? densityColorMAX : densityMAX;
	int gray = (colormap) ? 0 : 1;

	if (sigma !=0 && kernel % 2 == 1) {
		gaussianfiltermask(maskData, kernel, sigma);
		filter=1;
	}

	switch (mode) {
	 case MRC_MODE_BYTE:
         {
		char *data_array = (char *)mrc->pbyData;

		if(scale <= 0) {
			fmax = fmin = (float)data_array[0];
			for (i = 0; i<n ; i++) {
				fmax = MAX(fmax, data_array[i]);
				fmin = MIN(fmin, data_array[i]);
			}
		}
		min = fmin + pmin * scale / densitymax;
		max = fmin + pmax * scale / densitymax;
		scale = max - min;
		
		if (scale != 0)
		for (i=-1,j=0,t=0; t<n; t+=binning,j++) {
			if (j % n_w == 0) { 
				j=0; i++;
				if (i>0)
					t += off_w+w*(binning-1);
			}
			if (filter)
			{
				getMaskDataIndexes(maskindexes, kernel, t, w);
				for (f_val=0, index = 0; index < masksize; index++)
					if (maskindexes[index] != -1)
						f_val += data_array[maskindexes[index]] * maskData[index];
			}
			if (binning>1) 
				if (skip)
					f_val = data_array[t];
				else {
					getIndexes(indexes, binning, t, w) ;
					for (f_val=0,index=0; index<binningsize; index++)
						f_val += data_array[indexes[index]];
					f_val /= binningsize;
				}
			else
				f_val = data_array[t];

			f_val = (f_val-min)*densitymax/scale;
			tpixels[i][j] = setColorDensity(f_val, gray);

			if (binning>1)
				if (i>=(n_h-1) && j>=(n_w-1))
					break;
		}
         }
         break;
	 case MRC_MODE_SHORT:
         {
		short *data_array = (short *)mrc->pbyData;
		
		if(scale <= 0) {
			fmax = fmin = (float)data_array[0];
			for (i = 0; i < n; i++) {
				fmax = MAX(fmax, data_array[i]);
				fmin = MIN(fmin, data_array[i]);
			}
		}
		min = fmin + pmin * scale / densitymax;
		max = fmin + pmax * scale / densitymax;
		scale = max - min;
		
		if (scale != 0)
		for (i=-1,j=0,t=0; t<n; t+=binning,j++) {
			if (j % n_w == 0) { 
				j=0; i++;
				if (i>0)
					t += off_w+w*(binning-1);
			}
			if (filter)
			{
				getMaskDataIndexes(maskindexes, kernel, t, w);
				for (f_val=0, index = 0; index < masksize; index++)
					if (maskindexes[index] != -1)
						f_val += data_array[maskindexes[index]] * maskData[index];
			}
			if (binning>1) 
				if (skip)
					f_val = data_array[t];
				else {
					getIndexes(indexes, binning, t, w) ;
					for (f_val=0,index=0; index<binningsize; index++)
						f_val += data_array[indexes[index]];
					f_val /= binningsize;
				}
			else
				f_val = data_array[t];

			f_val = (f_val-min)*densitymax/scale;
			tpixels[i][j] = setColorDensity(f_val, gray);

			if (binning>1)
				if (i>=(n_h-1) && j>=(n_w-1))
					break;
		}
         }
         break;
	 case MRC_MODE_FLOAT:
         {
		float *data_array = (float *)mrc->pbyData;

		if(scale <= 0) {
			fmax = fmin = data_array[0];
			for (i = 0; i < n; i++) {
				fmax = MAX(fmax, data_array[i]);
				fmin = MIN(fmin, data_array[i]);
			}
		}

		min = fmin + pmin * scale / densitymax;
		max = fmin + pmax * scale / densitymax;
		scale = max - min;
		
		if (scale != 0)
		for (i=-1,j=0,t=0; t<n; t+=binning,j++) {
			if (j % n_w == 0) { 
				j=0; i++;
				if (i>0)
					t += off_w+w*(binning-1);
			}
			if (filter)
			{
				getMaskDataIndexes(maskindexes, kernel, t, w);
				for (f_val=0, index = 0; index < masksize; index++)
					if (maskindexes[index] != -1)
						f_val += data_array[maskindexes[index]] * maskData[index];
			}
			else if (binning>1) 
				if (skip)
					f_val = data_array[t];
				else {
					getIndexes(indexes, binning, t, w) ;
					for (f_val=0, index=0; index<binningsize; index++)
						f_val += data_array[indexes[index]];
					f_val /= binningsize;
				}
			else
				f_val = data_array[t];

			f_val = (f_val-min)*densitymax/scale;
			tpixels[i][j] = setColorDensity(f_val, gray);

			if (binning>1)
				if (i>=(n_h-1) && j>=(n_w-1))
					break;
		}
         }
         break;
	 case MRC_MODE_UNSIGNED_SHORT:
         {
		unsigned short *data_array = (unsigned short *)mrc->pbyData;

		if(scale <= 0) {
			fmax = fmin = data_array[0];
			for (i = 0; i < n; i++) {
				fmax = MAX(fmax, data_array[i]);
				fmin = MIN(fmin, data_array[i]);
			}
		}

		min = fmin + pmin * scale / densitymax;
		max = fmin + pmax * scale / densitymax;
		scale = max - min;

		if (scale != 0)
		for (i=-1,j=0,t=0; t<n; t+=binning,j++) {
			if (j % n_w == 0) { 
				j=0; i++;
				if (i>0)
					t += off_w+w*(binning-1);
			}
			if (filter)
			{
				getMaskDataIndexes(maskindexes, kernel, t, w);
				for (f_val=0, index = 0; index < masksize; index++)
					if (maskindexes[index] != -1)
						f_val += data_array[maskindexes[index]] * maskData[index];
			}
			if (binning>1) 
				if (skip)
					f_val = data_array[t];
				else {
					getIndexes(indexes, binning, t, w) ;
					for (f_val=0,index=0; index<binningsize; index++)
						f_val += data_array[indexes[index]];
					f_val /= binningsize;
				}
			else
				f_val = data_array[t];

			f_val = (f_val-min)*densitymax/scale;
			tpixels[i][j] = setColorDensity(f_val, gray);

			if (binning>1)
				if (i>=(n_h-1) && j>=(n_w-1))
					break;
		}
         }
         break;
	}
}

/* get pixel indexes from a  binning factor applied to a pixel index */
int getIndexes(int indexes[], int binning, int index, int imagewidth) {
	int	i=0,
		b_w=0,
		b_h=0;

	for(b_w=0; b_w<binning; b_w++)
                for(b_h=0; b_h<binning; b_h++, i++)
                        indexes[i] = index + b_w*imagewidth + b_h;
}

/* get pixel indexes from a mask (kernelxkernel) applied to a pixel index */
int getMaskDataIndexes(int indexes[], int kernel, int index, int imagewidth) {
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

int gdreadMRCHeader(gdIOCtx *io_ctx, MRCHeader *pMRCHeader) {
	gdGetBuf(pMRCHeader, MRC_HEADER_SIZE, io_ctx);
	if((pMRCHeader->nx < 0) || (pMRCHeader->ny < 0) || (pMRCHeader->nz < 0) ||
		(pMRCHeader->mode < 0) || (pMRCHeader->mode > 4))
			return -1; /* This is not a valid pMRCHeader header */
	return 1 ;
}

int gdreadMRCData(gdIOCtx *io_ctx, MRC *pMRC) {
	unsigned int uElementSize = 0;
	unsigned int uElements = 0;

	uElements = pMRC->header.nx * pMRC->header.ny * pMRC->header.nz;

	switch(pMRC->header.mode) {
		case MRC_MODE_BYTE:
			uElementSize = sizeof(char);
			break;
		case MRC_MODE_SHORT:
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
	

	if((pMRC->pbyData = malloc(uElements*uElementSize)) == NULL)
		pMRC->pbyData = malloc(uElements*uElementSize);

	gdGetBuf(pMRC->pbyData, (uElements*uElementSize), io_ctx);
	
	return 1;
}

int gdloadMRC(gdIOCtx *io_ctx, MRC *pMRC) {
	unsigned int uElementSize = 0;
	unsigned int uElements = 0;
	unsigned int fuByteOrder = LITTLE_ENDIAN_DATA;

	if (!gdreadMRCHeader(io_ctx, &(pMRC->header)))
		return -1;

	uElements = pMRC->header.nx * pMRC->header.ny * pMRC->header.nz;

	switch(pMRC->header.mode) {
		case MRC_MODE_BYTE:
			uElementSize = sizeof(char);
			break;
		case MRC_MODE_SHORT:
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
	

	if((pMRC->pbyData = malloc(uElements*uElementSize)) == NULL)
		pMRC->pbyData = malloc(uElements*uElementSize);

	gdGetBuf(pMRC->pbyData, (uElements*uElementSize), io_ctx);
	
	return 1;
}
