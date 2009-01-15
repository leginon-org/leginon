#ifndef libcv_ctf
#define libcv_ctf

#include "Array.h"
#include "Ellipse.h"
#include "MRC.h"
#include "Image.h"
#include "util.h"
#include "cvtypes.h"
#include <fftw3.h>
#include <math.h>
#include "geometry.h"
#include <gsl/gsl_math.h>
#include <gsl/gsl_linalg.h>
#include <gsl/gsl_blas.h>
#include <gsl/gsl_eigen.h>
#include <gsl/gsl_multimin.h>

typedef struct CTFST {
	
	char * imgpath;
	
	f64 defocus_x;
	f64 defocus_y;
	f64 astig_angle;
	f64 amplitude;
	f64 volts;
	f64 lambda;
	f64 size;
	f64 apix;
	f64 scale;
	
	f64 * ctf1d;
	f64 * ctfsynth1d;
	f64 * background1d;
	f64 * envelope1d;
	f64 ctf1dscale;
	f64 ctf1dapix;
	u32 ctf1dsize;

	
	f64 * ctf2d;
	f64 * ctfsynth2d;
	f64 * background2d;
	f64 * envelope2d;
	f64 ctf2dapix;
	u32 ctf2drows;
	u32 ctf2dcols;
		
} * CTF;

@interface Array ( CTF_Functions )

-(id) correctCTFdf1:(f64)df1 df2:(f64)df2 dfr:(f64)dfr ac:(f64)ac kv:(f64)kv cs:(f64)cs ap:(f64)ap;
-(id) powerSpectrum;
-(id) ellipse1DAvg:(EllipseP)ellipse;

@end

void ctf2_calcv( f64 c[], f64 ctf[], u64 size );
f64 ctf_norm( f64 fit_data[], f64 ctf_p[], f64 ctf[], f64 norm[], u32 size );
f64 calculate_score(f64 c1[], f64 c2[], u32 lcut, u32 rcut );
ArrayP ctfNormalize( ArrayP fit_data, ArrayP ctf_params );
void estimateDefocus( ArrayP fit_data, ArrayP ctf_params );
void peakNormalize( f64 values[], u32 size );
ArrayP fitNoise( ArrayP fit_data );
ArrayP fitEnvelope( ArrayP fit_data );
f64 getTEMLambda( f64 volts );
f64 getTEMVoltage( f64 lambda );
f64 ctf_calc( f64 c[], f64 x );
void fit2DCTF( ArrayP image, f64 d1, f64 d2, f64 th, f64 apix, f64 kv, f64 cs, f64 ac );
f64 positionForPeak( f64 c[], u32 peak_pos );
f64 defocusForPeak( f64 c[], f64 peak_pos, u32 peak_num );
ArrayP generate2DCTF( f64 df1, f64 df2, f64 theta, u32 rows, u32 cols, f64 apix, f64 cs, f64 kv, f64 ac );
ArrayP g2DCTF( f64 df1, f64 df2, f64 theta, u32 rows, u32 cols, f64 apix, f64 cs, f64 kv, f64 ac );

#endif
