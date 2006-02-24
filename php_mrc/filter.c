/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource                          |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#include "php.h"
#include "gd.h"
#include "filter.h"

/* {{{ int setDensity(float value) { */
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
/* }}} */

/* {{{ int setRGBDensity(float R, float G, float B) { */
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
/* }}} */

/* {{{ int setColorDensity(float value, int bw) { */
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
/* }}} */

/* {{{ unsigned char getDensity(int pixelvalue) { */
unsigned char getDensity(int pixelvalue) {
	return ((pixelvalue) & 0x0000FF);
}
/* }}} */

/* {{{ int getLog(int pixelvalue) { */
int getLog(int pixelvalue) {
	unsigned char density;
	float logvalue;
	density = getDensity(pixelvalue);
	if (density == 0)
		density = 1;
	logvalue = log(density) * densityMAX / log(densityMAX);
	return setDensity(logvalue);
}
/* }}} */


/* filter a gd image using gaussian smoothing */
/* {{{ void filtergaussian(gdImagePtr im, int kernel, float factor) { */
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

	double	*maskData;

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

        maskData = malloc(sizeof(double)*maskWidth*maskHeight);

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

					index = x + y * maskWidth;
					ndensityR += densityR * maskData[index];
					ndensityG += densityG * maskData[index];
					ndensityB += densityB * maskData[index];
				}
			}
			gdImageSetPixel (im, w, h, setRGBDensity(ndensityR, ndensityG, ndensityB));
		}
	}

	free(maskData);

}
/* }}} */

/* {{{ void gaussianfiltermask(double *maskData, int kernel, float sigma) { */
void gaussianfiltermask(double *maskData, int kernel, float sigma) {

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
/* }}} */
