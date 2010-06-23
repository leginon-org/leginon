/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource                          |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#include "php.h"
#include "gd_unbundled.h"
#include "gd.h"
#include "filter.h"

/* {{{ int setDensity(float value) { */
int setDensity(float value) {
	int density;
	if (value > DENSITY_MAX) {
		value = DENSITY_MAX;
	} else if (value < DENSITY_MIN) {
		value = DENSITY_MIN;
	}
	unsigned char pixval = (unsigned char)value;
	density = ((pixval << 16) + (pixval << 8) + pixval);
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
	logvalue = log(density) * DENSITY_MAX / log(DENSITY_MAX);
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
			gdImageSetPixel (im, w, h, setDensity(ndensityR));
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
