/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource				 |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#include "php.h"
#include "gd.h"
#include "filter.h"

int setDensity(float value) {
	int density;
	if (value > densityMAX) {
		value = densityMAX;
	} else if (value < densityMIN) {
		value = densityMIN;
	}
	unsigned char pixval = (unsigned char)value;
	density = ((pixval << 16) + (pixval << 8) + pixval);
	return density;
}

int setRGBDensity(float R, float G, float B) {
	int color;
	R = (R > densityMAX) ? densityMAX : ((R < densityMIN) ? densityMIN : R );
	G = (G > densityMAX) ? densityMAX : ((G < densityMIN) ? densityMIN : G );
	B = (B > densityMAX) ? densityMAX : ((B < densityMIN) ? densityMIN : B );

	unsigned char pixR= (unsigned char)R;
	unsigned char pixG= (unsigned char)G;
	unsigned char pixB= (unsigned char)B;

	color = ((pixR << 16) + (pixG << 8) + pixB);
	return color;
}

int setColorDensity(float value, int bw) {
	int density;
	if (bw) {
		return setDensity(value);
	}
	if (value > 1274 ) {
		value = 1274;
	} else if (value < 0 ) {
		value = 0;
	}
//	unsigned char pixva = (unsigned char)value;
//	density = ((pixva << 16) + (pixva << 8) + pixva);
//	return density;
	// int pixval = (int)(value/255);
	
	unsigned char pixval = value;
	pixval = (unsigned char)((int)value % 255);
        if (value<255) {
                density = ((255 << 16) + (pixval << 8) + 0);
        } else if (value<255*2) {
                density = (((255-pixval) << 16) + (255 << 8) + 0);
        } else if (value<255*3) {
                density = ((0 << 16) + (255 << 8) + pixval);
        } else if (value<255*4) {
                density = ((0 << 16) + ((255-pixval) << 8) + 255);
        } else if (value<=255*5) {
                density = ((pixval << 16) + (0 << 8) + 255);
        }
	return density;
}

unsigned char getDensity(int pixelvalue) {
	return ((pixelvalue) & 0x0000FF);
}

int getLog(int pixelvalue) {
	unsigned char density;
	float logvalue;
//	density = densityMAX - getDensity(pixelvalue);
//	logvalue = densityMAX - log(density) * densityMAX / log(densityMAX);
	density = getDensity(pixelvalue);
	if (density == 0)
		density = 1;
	logvalue = log(density) * densityMAX / log(densityMAX);
	return setDensity(logvalue);
}


/*
function RelTranslate($a) {
if( $a==0 ) $a=1;
$a=(log($a));

$ml = log(255);

$a = $a*255/$ml;

return $a;
}

*/

/* resize a gd image */
gdImagePtr resize(gdImagePtr im, int w, int h, int n_w, int n_h ) {
	if (n_w > 0 && n_h > 0 ) {
		gdImagePtr im_tmp;
		im_tmp = gdImageCreateTrueColor(n_w, n_h);
		gdImageFastCopyResized (im_tmp, im, 0, 0, 0, 0, n_w, n_h, w, h);
		gdImageDestroy(im);
		return im_tmp;
	} else {
		return im;
	}
}

/* filter a gd image using gaussian smoothing */
void filtergaussian(gdImagePtr im, int kernel, float factor) {

	int	maskWidth=kernel,
		maskHeight=kernel,
		x=0,
		y=0,
		h = 0,
		w = 0,
		sx = im->sx,
		sy = im->sy,
		index = 0;
	int c;

	double	maskData[maskWidth*maskHeight];

	float	density,
		ndensity,
		densityR,
		densityG,
		densityB,
		densityA,
		ndensityR,
		ndensityG,
		ndensityB,
		ndensityA;

	if (factor==0 || kernel % 2 != 1)
		return;

	gaussianfiltermask(maskData, kernel, factor);

	for (h = 0; h < sy; h++) {
		for (w = 0; w < sx; w++) {
			ndensity = 0; 
			ndensityR = 0;
			ndensityG = 0;
			ndensityB = 0;

			for (y = 0; y < maskHeight; y++) {
				for (x = 0; x < maskWidth; x++) {
					c = gdImageGetPixel(im, (w+x-maskWidth/2), (h+y-maskHeight/2));
					densityR = gdTrueColorGetRed(c);
					densityG = gdTrueColorGetGreen(c);
					densityB = gdTrueColorGetBlue(c);

			//		density = getDensity(
			//				gdImageGetPixel(im, (w+x-maskWidth/2), (h+y-maskHeight/2) )
			//			);
					index = x + y * maskWidth;
					// ndensity += density * maskData[index];
					ndensityR += densityR * maskData[index];
					ndensityG += densityG * maskData[index];
					ndensityB += densityB * maskData[index];
				}
			}
	//		im->tpixels[h][w]=setDensity(ndensity);
			im->tpixels[h][w]=setRGBDensity(ndensityR, ndensityG, ndensityB);
		}
	}

}

void gaussianfiltermask(double maskData[], int kernel, float sigma) {

	int	x,
		y;

	double	cx = 0,
		cy = 0,
		r = 0,
		mult = 0;

	if (sigma==0 || kernel % 2 != 1)
		return;

	for(y = 0; y < kernel; y++) {
                for(x = 0; x < kernel; x++) {
                        cx = (double)x - (double)(kernel - 1) / 2.0;
                        cy = (double)y - (double)(kernel - 1) / 2.0;
                        r = cx * cx + cy * cy;
                        mult += exp(r/(-2*(sigma*sigma)));
                }
        }

        mult = 1.0 / mult;

        for(y = 0; y < kernel; y++) {
                for(x = 0; x < kernel; x++) {
                        cx = (double)x - (double)(kernel - 1) / 2.0;
                        cy = (double)y - (double)(kernel - 1) / 2.0;
                        r = cx * cx + cy * cy;
                        maskData[y * kernel + x] = mult * exp(r/(-2*(sigma*sigma)));
                }
        }
	
}

void
gdImageFastCopyResized (gdImagePtr dst, gdImagePtr src, int dstX, int dstY, int srcX, int srcY, int dstW, int dstH, int srcW, int srcH)
{
  int x, y;
  int tox, toy;
  int ydest;
  int i;
  /* Stretch vectors */
  int *stx;
  int *sty;
  /* We only need to use floating point to determine the correct
     stretch vector for one line's worth. */
  double accum;
  stx = (int *) malloc (sizeof (int) * srcW);
  sty = (int *) malloc (sizeof (int) * srcH);
  accum = 0;
  for (i = 0; (i < srcW); i++)
    {
      int got;
      accum += (double) dstW / (double) srcW;
      got = (int) floor (accum);
      stx[i] = got;
      accum -= got;
    }
  accum = 0;
  for (i = 0; (i < srcH); i++)
    {
      int got;
      accum += (double) dstH / (double) srcH;
      got = (int) floor (accum);
      sty[i] = got;
      accum -= got;
    }

  toy = dstY;
  for (y = srcY; (y < (srcY + srcH)); y++)
    {
      for (ydest = 0; (ydest < sty[y - srcY]); ydest++)
	{
	  tox = dstX;
	  for (x = srcX; (x < (srcX + srcW)); x++)
	    {
	      int mapTo;
	      if (!stx[x - srcX])
		{
		  continue;
		}

		mapTo = src->tpixels[y][x];

	      for (i = 0; (i < stx[x - srcX]); i++)
		{
			dst->tpixels[toy][tox]=mapTo;
		  tox++;
		}
	    }
	  toy++;
	}
    }
  free (stx);
  free (sty);
}

/* copy pixels from img_src -> ima_dst */
void copytpixels(gdImagePtr im_dst, gdImagePtr im_src)
{
  int i,j;
  if (im_dst->tpixels && im_src->tpixels)
      for (i = 0; (i < im_src->sy); i++)
	      for (j = 0; (j < im_src->sx); j++)
          		im_dst->tpixels[i][j] = im_src->tpixels[i][j];
}

/* log scale */
void gdLogScale(gdImagePtr im_src) {
  int i,j;
  if (im_src->tpixels)
      for (i = 0; (i < im_src->sy); i++)
	      for (j = 0; (j < im_src->sx); j++)
          		im_src->tpixels[i][j] = getLog(im_src->tpixels[i][j]);
}
