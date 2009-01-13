#ifndef libcv_image
#define libcv_image

#include "Array.h"
#include <fftw3.h>
#include <math.h>

#define DEFAULT_IMAGE_TYPE TYPE_F64

@interface Array ( Image_Functions )

-(void) scaleFrom: (f64)newmin to: (f64)newmax ;

-(id) gaussianBlurWithSigma:(f64)sigma ;

-(void) gaussianBlurWithSigmaR:(f64)sigma;

-(void) binBy: (u32)bin ;

-(void) subtractImage: (id)image ;

-(void) addImage: (id)image ;

-(id)   buildDoGFrom: (f64)fsigma to: (f64)tsigma sampled: (u32)samples ;

-(void) multiplyBy: (f64)scalar ;

-(void) divideBy: (f64)scalar ;

-(void) edgeBlur:(u32)pixels;

-(void) cannyEdgesWithUpperTreshold:(f64)upper lowerTreshold:(f64)lower;

-(void) floodFillFrom:(f64)lower to:(f64)upper usingConnectivity:(u08)n_conn;

-(id) generatePowerSpectrum;

-(void) boxSum;

-(void) boxBlurSize:(u32)s;

-(id) fftc;

-(id) ifftc;

-(id) fftshift;

-(id) c2rfftc;

-(id) r2cfftc;

/*
- (void) map_reset ;

- (void) label_reset ;

- (void) map_removeBorderPixels ;

- (void) map_tresholdFrom: (f64)min to: (f64)max ;

- (void) map_labelsWithSizesFrom: (u32)min to: (u32)max ;

- (void) label_connectedComponentsFromMap ;
*/

@end

#define CV_CONNECT_ALL		1
#define CV_CONNECT_ADJACENT	0

void boxSum( f64 xi[], const u32 s_ndim, const u32 s_dims[], const u32 s_stps[] );
u08 * floodFill( f64 src[], u32 s_ndim, u32 s_dims[], u32 s_stps[], f64 lt, f64 ut, u08 n_conn );
void boxBlur( f64 xi[], const u32 s_ndim, const u32 s_dims[], const u32 s_stps[], u32 s );
f64 interpolate( f64 *image, f64 row, f64 col, u32 rows, u32 cols );
void gaussian1d( f64 * data, s32 minl, s32 maxl, f64 sigma );

void restoreFFTWisdom();
void saveFFTWisdom();

#endif
