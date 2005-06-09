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
gdImagePtr resize(gdImagePtr im, int w, int h, int n_w, int n_h );
void filtergaussian(gdImagePtr im, int masksize, float factor);
void gdImageFastCopyResized (gdImagePtr dst, gdImagePtr src, int dstX, int dstY, int srcX, int srcY, int dstW, int dstH, int srcW, int srcH);
void copytpixels(gdImagePtr im_dst, gdImagePtr im_src);
void gaussianfiltermask(double *maskData, int kernel, float sigma);
void gdLogScale(gdImagePtr im_src);
