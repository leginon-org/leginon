#ifndef IMGDEF_H
#define IMGDEF_H

#include<stdio.h>
#include<stdlib.h>
#include<math.h>
#include<string.h>

#ifndef BOOLEAN
   typedef int BOOLEAN;
#endif

#ifndef TRUE
  #define TRUE    1
#endif

#ifndef FALSE
  #define FALSE   0
#endif

#ifndef EPSILON
#define EPSILON 1.0e-7
#define FZ(x) ((x) < EPSILON && (-(x)) < EPSILON)
#endif

#ifndef M_PI
  #define M_PI        3.14159265358979323846
#endif

#ifndef M_PI_2
  #define M_PI_2      1.57079632679489661923
#endif

/* sqrt(2*M_PI) : used in calculating likelihoods. */
#ifndef SQRT_2_PI
  #define SQRT_2_PI   2.50662827463100050241
#endif

//float mh_sqrarg;  /* used in the Macro SQR(). */
//#define SQR(a)  ((mh_sqrarg=(float)(a)) == 0.0 ? 0.0 : mh_sqrarg*mh_sqrarg)

#ifndef BOOSTBLURFACTOR
#define BOOSTBLURFACTOR 90.0
#endif

#ifndef EDGE_VALUES
#define EDGE_VALUES
#define NOEDGE          255
#define POSSIBLE_EDGE   128
#define EDGE            0
#define BLACK NOEDGE
#endif

#ifndef SCALE_TAG
#define SCALE_TAG
#define NO_SCALE 	0
#define DO_SCALE 	1
#endif

#ifndef DRAW_IMAGE_MODE
  #define DRAW_IMAGE_MODE
  #define IDRAW_OVERWRITE       0
  #define IDRAW_XOR             1
  #define IDRAW_AND             2
  #define IDRAW_OR              3
#endif

#ifndef VERBOSE
#define VERBOSE 0
#endif

#ifndef PRUNECODE
#define PRUNECODE
#define BYLENGTH 	0
#define BYSIZE          1
#endif

#ifndef INTERPOLATION
#define INTERPOLATION
#define NNEIGHBOR 	1
#define LINEAR          2
#endif

void gprintf(char *format, ...);
                                                                             
void error_exit(char *format, ...);

void * malloc1(unsigned size);                                                                             

void * calloc1(unsigned n, unsigned size);

void * realloc1(void *buf, unsigned size);

void linear_scaling_float( float* image, int nsize, float* outimg, float lo, float hi);

void histogram_equalization(float *image, int image_size, unsigned int Dm);

void binary_thresholding_float( float* image, long nsize, float lo, float hi,
                                float foreground, float background);

void img_draw_pixel(unsigned char *lpstrImgBits, int xsize, int ysize,int x, int y,
                    unsigned char colorValue, int mode);

#endif /* IMGDEF_H */ 
