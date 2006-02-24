/*
  +----------------------------------------------------------------------+
  | image filtering tools for GD image resource				 |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

#define densityMAX 255
#define densityColorMAX 1274
#define densityMIN 0

int setDensity(float value);
int setColorDensity(float value, int bw);
int setRGBDensity(float R, float G, float B);
unsigned char getDensity(int density);
int getLog(int pixelvalue);
void filtergaussian(gdImagePtr im, int masksize, float factor);
void gaussianfiltermask(double *maskData, int kernel, float sigma);
void gdLogScale(gdImagePtr im_src);
