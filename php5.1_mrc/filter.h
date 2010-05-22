/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource				 |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#define DENSITY_MIN 0
#define DENSITY_MAX 255

int setDensity(float value);
unsigned char getDensity(int density);
int getLog(int pixelvalue);
void filtergaussian(gdImagePtr im, int masksize, float factor);
void gaussianfiltermask(double *maskData, int kernel, float sigma);
void gdLogScale(gdImagePtr im_src);
