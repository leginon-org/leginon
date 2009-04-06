#include "cvtypes.h"
#include "Array.h"
#include "MRC.h"
#include "PGM.h"
#include "Image.h"
#include "Ellipse.h"
#include "util.h"
#include "getopts.h"
#include "ctf.h"
#include "geometry.h"
#include <gsl/gsl_math.h>
#include <gsl/gsl_linalg.h>
#include <gsl/gsl_blas.h>
#include <gsl/gsl_eigen.h>
#include <gsl/gsl_multimin.h>

f64 calcBackDrift( f64 values[], u32 rad, f64 mins, f64 maxs );

f64 highest_res( f64 ctf_p[], f64 size, f64 apix ) {
	
	// Best way to solve this is too find the roots of the derivative of ctf, where
	// the derivative is equal to pi/2 or -pi/2.  Since the derivative of CTF is cubic
	// we need the find the cubic roots, ugh!
	
	f64 df = ctf_p[0];
	f64 ac = ctf_p[1];
	f64 lm = ctf_p[2];
	f64 cs = ctf_p[3];
	f64 ap = ctf_p[4];
	
	// dCTF = 2PI*lm*lm*lm*x^3 + 2PI*lm*df*x - PI/2
	// x^3 + ax^2 + bx + c = 0
	u32 i;
	for(i=0;i<10000;i++) {
//		f64 x = i*ap;
		f64 x1 = ((f64)i-0.5)*ap;
		f64 x2 = ((f64)i+0.5)*ap;
//		f64 d1 = 2*PI*lm*x*(lm*lm*x*x*cs+df);
		f64 v1 = PI*lm*x1*x1*(0.5*lm*lm*x1*x1*cs+df)-asin(ac);
		f64 v2 = PI*lm*x2*x2*(0.5*lm*lm*x2*x2*cs+df)-asin(ac);
		f64 d2 = v2 - v1;
		if ( ABS(d2) > PI/2.0 ) break;
//		if ( ABS(d1) > PI/2.0 ) break;
	}
	
	f64 highest_res = 1.0/(i*ap);
	
	fprintf(stderr,"Resolution limit at current defocus %e and size %f is %e %d\n",ctf_p[0],ap,highest_res,i);
	
	return highest_res;
	
}

ArrayP ctfNormalize( ArrayP fit_data, ArrayP ctf_params );
ArrayP createCTFParams( f64 defocus, f64 apix, f64 size, f64 ac, f64 kv, f64 cs );
ArrayP createRadialAverage( ArrayP image, EllipseP ellipse );
void generate1DCTF( f64 df, u32 size, f64 apix, f64 cs, f64 kv, f64 dfs[] );
u32 peakReduce( f64 * data, s32 size, f64 sigma, s32 min_peaks, s32 max_peaks );
void peakCount( f64 * data, s32 size, s32 * min_peaks, s32 * max_peaks );
f64 detectMirrors( f64 * image, u32 rows, u32 cols, u32 ang_search, f64 ang_spacing );
ArrayP minMaxPeakFind( ArrayP image );
ArrayP generate2DCTF( f64 df1, f64 df2, f64 theta, u32 rows, u32 cols, f64 apix, f64 cs, f64 kv, f64 ac );
void normalizeValues( f64 values[], u32 size );
u32 minPosition( f64 values[], u32 size );
u32 maxPosition( f64 values[], u32 size );
void ctfFromParams( ArrayP ctf_params, ArrayP curve );
void fitCTF( ArrayP fit_data, ArrayP ctf_params );

int main (int argc, char **argv) {
	
	COMPILE_INFO;

	srand((unsigned)time(NULL));
	
	struct options opts[] = {
		{ 1, "image",	"Pathname to MRC image file", 					"i", 1 },
		{ 2, "apix",	"Angstroms per pixel of input image", 			"a", 1 },
		{ 3, "sabr",	"Spherical Aberation of microcope in mm",		"c", 1 },
		{ 4, "kvolts",	"Voltage of microscope in kv",					"k", 1 },
		{ 5, "binby",	"Ammount to bin input image",						"b", 1 },
		{ 6, "amp",		"Initial Amplitude Contrast",						"m", 1 },
		{ 7, "edge",	"Edge Parameters",									"e", 1 },
		{ 8, "out",		"Out Path for data",									"o", 1 },
		{ 0, NULL,		NULL,										   NULL, 0 }
	};
	
	char arg[256];
	s32 s_s = 0;
	
	ArrayP image = nil;
	
	f64 ac = 0.3;
	f64 apix = 1.55;
	f64 cs = 2.0;
	f64 kv = 120.0;
	u32 binby = 2;
	
	f64 edge_blur = 6.0;
	f64 edge_mint = 0.00001;
	f64 edge_maxt = 0.0008;
	
	f32 t0 = CPUTIME;	
	f32 t1 = CPUTIME;
	
	while ( ( s_s = getopts(argc,argv,opts,arg) ) != 0 ) {
		switch ( s_s ) {
			case -2:
				fprintf(stderr,"Argument %s is not understood\n",arg);
				return -1;
			case -1:
				fprintf(stderr,"No memory for parsing, exiting!!!\n");
				return -1;
			case  1:
				t1 = CPUTIME;
				fprintf(stderr,"Reading Image %s: ",arg);	
				image = [Array readMRCFile:arg];
				[image printInfoTo:stderr];
				[image setFlag:CV_ARRAY_DATA_SCALES to: TRUE];
				[image setTypeTo: TYPE_F64];
				fprintf(stderr,"\t\t\tDONE in %2.2f seconds\n",CPUTIME-t1);
				break;
			case  2:
				if ( sscanf(arg,"%lf",&apix) != 1 ) return -1;
				break;
			case  3:
				if ( sscanf(arg,"%lf",&cs) != 1 ) return -1;
				break;
			case  4:
				if ( sscanf(arg,"%lf",&kv) != 1 ) return -1;
				break;
			case  5:
				sscanf(arg,"%d",&binby);
				break;
			case  6:
				sscanf(arg,"%lf",&ac);
				break;
			case  7:
				sscanf(arg,"%lf,%lf",&edge_blur,&edge_maxt);
				edge_mint = 0.1*edge_maxt;
				break;	
			default:
				break;
		}
	}

	fprintf(stderr,"Processing image with %d %d pixels\n",[image sizeOfDimension:0],[image sizeOfDimension:1]);
	fprintf(stderr,"APIX: %f  KV: %f  CS: %f  \n",apix,kv,cs);
	
	t1 = CPUTIME;
	fprintf(stderr,"Binning image by %d pixels...",binby);
	if ( binby != 1 && binby < 8 ) [image binBy:binby];
	fprintf(stderr,"\t\t\tDONE in %2.2f seconds\n",CPUTIME-t1);
	
	t1 = CPUTIME;
	u32 off = 100;
	fprintf(stderr,"Blurring %d edge pixels...",off);
	[image edgeBlur:off];
	fprintf(stderr,"\t\t\tDONE in %2.2f seconds\n",CPUTIME-t1);

//----------------------------------------------------------------------------
	
	t1 = CPUTIME;
	fprintf(stderr,"Generating power spectrum...");	
	[image generatePowerSpectrum];
	u32 postbin = MIN([image sizeOfDimension:0],[image sizeOfDimension:1])/1024;
	if ( postbin > 1 ) {
		fprintf(stderr,"binning by %d...",postbin);
		[image binBy:postbin];
	}
	fprintf(stderr,"\t\t\tDONE in %2.2f seconds\n",CPUTIME-t1);
	
//----------------------------------------------------------------------------
	
	t1 = CPUTIME;
	fprintf(stderr,"Finding edges for ellipse fitting...");	
	ArrayP edges = [image deepCopy];
	[edges printInfoTo:stderr];
	[edges gaussianBlurWithSigma:edge_blur];
	u32 edge_count = cannyedges2d([edges data],[edges sizeOfDimension:1],[edges sizeOfDimension:0],edge_mint,edge_maxt,5.0);

	fprintf(stderr,"\t\tDONE in %2.2f seconds (%d edges)\n",CPUTIME-t1,edge_count);

//----------------------------------------------------------------------------

	t1 = CPUTIME;
	fprintf(stderr,"Using RANSAC to find ellipse parameters...");
	

	f64 fit_treshold = 0.75;
	f64 min_percent = 0.001;
	f64 fit_percent = 0.99;
	f64 max_iterations = 100000;

	EllipseP ellipse = ellipseRANSAC(edges,fit_treshold,min_percent,fit_percent,max_iterations);
	
	if ( ellipse == nil ) fprintf(stderr,"NO ELLIPSE FITTING DONE!!!!!!!!!!");
	
	if ( CPUTIME-t1 > 0.0 ) {
		char name[256];
		ArrayP image_copy = [image deepCopy];
		[image_copy gaussianBlurWithSigma:edge_blur];
		[[image_copy ln] scaleFrom:0.0 to:1.0];
		[ellipse drawInArray:image_copy];
		[edges scaleFrom:0.0 to:2.0];
		[edges addImage:image_copy];
		sprintf(name,"%s.edge.mrc",basename([image name]));
		if ( [edges writeMRCFile:name] == FALSE ) fprintf(stderr,"\tWrite Failed\n");
		[image_copy release];
	}
	
	fprintf(stderr,"\t\t\t\t\t\tDONE in %2.2f seconds\n",CPUTIME-t1);
	
//----------------------------------------------------------------------------
	
	t1 = CPUTIME;
	fprintf(stderr,"Creating 1D radial average...");
	ArrayP radial_average = createRadialAverage(image,ellipse);
	fprintf(stderr,"\t\t\t\t\t\tDONE in %2.2f seconds\n",CPUTIME-t1);
	
//----------------------------------------------------------------------------
	
	t1 = CPUTIME;
	fprintf(stderr,"Estimating initial defocus...");

	ArrayP ctf_params = createCTFParams( 0.0, apix*binby, [image sizeOfDimension:0], ac, kv, cs );

	estimateDefocus(radial_average,ctf_params);

	ArrayP radial_average_norm = ctfNormalize(radial_average,ctf_params);
	
	fprintf(stderr,"\t\t\t\t\t\tDONE in %2.2f seconds\n",CPUTIME-t1);

//----------------------------------------------------------------------------

	t1 = CPUTIME;
	fprintf(stderr,"Fine-tuning defocus...");
	
	u32 i, size = [radial_average_norm sizeOfDimension:0];
	f64 * v_data = [radial_average_norm getRow:0];
	gaussian1d(v_data,0,size-1,4.0);
	
	fitCTF(radial_average_norm,ctf_params);

	f64 * ctf_p = [ctf_params data];
	
	f64 df1 = ctf_p[0];
	f64 ac1 = ctf_p[1];
	f64 lm1 = ctf_p[2];
	f64 cs1 = ctf_p[3];
	f64 ap1 = ctf_p[4];

	f64 dp1 = positionForPeak(ctf_p,1);
	f64 dp2 = dp1 * [ellipse major_axis]/[ellipse minor_axis];
	f64 df2 = defocusForPeak(ctf_p,dp2,1);
	
	f64 * c_data = NEWV(f64,size);
	
	peakNormalize(v_data,size);
	ctf2_calcv(ctf_p,c_data,size);
	
	f64 lcut = 50e-10;
	f64 rcut = 10e-10;
	
	lcut = MAX(0,(1.0/lcut)*(1.0/ap1));
	rcut = MIN(size-1,(1.0/rcut)*(1.0/ap1));
	
	fprintf(stderr,"\tCalculating confidence score from %f to %f\n",lcut,rcut);
	
	f64 confidence = calculate_score(v_data,c_data,lcut,rcut);
	
	fprintf(stderr,"\t\t\tDONE, Total Time: %2.2f\n",CPUTIME-t0);
	
	fprintf(stderr,"\tFinal Params:\n");
	fprintf(stderr,"\tDefocus: %2.5f %2.5f %2.5f\n",df1*1e6,df2*1e6,[ellipse rotation]*DEG);
	fprintf(stderr,"\tAmplitude Contrast: %2.2f%%\n",ac1*100);
	fprintf(stderr,"\tVoltage: %3.0f kv\n",getTEMVoltage(lm1)/1000.0);
	fprintf(stderr,"\tSpherical Aberration: %2.2fmm\n",cs1*1000.0);
	fprintf(stderr,"\tAngstroms per pixel: %2.2f\n",1e10*0.5/([radial_average numberOfElements]*ap1));
	fprintf(stderr,"\tConfidence Score: %2.2f\n",confidence);
	
	if ( isnan([ellipse rotation]) || isinf([ellipse rotation]) ) [ellipse setRotation:0.0];
	if ( isnan(df1) || isinf(df1) ) df1 = 0.0;
	if ( isnan(df2) || isinf(df2) ) df2 = 0.0;
	if ( isnan(ac1) || isinf(ac1) ) ac1 = 0.0;
	
	char name[1024];
	sprintf(name,"%s.ctf.txt",basename([image name]));
	FILE * fp = fopen(name,"w");
	
	fprintf(fp,"\tFinal Params for image: %s\n",[image name]);	
	fprintf(fp,"\tFinal Defocus: %e %e %e\n",df1,df2,[ellipse rotation]);
	fprintf(fp,"\tAmplitude Contrast: %e\n",ac1);
	fprintf(fp,"\tVoltage: %e\n",getTEMVoltage(lm1)/1.0e3);
	fprintf(fp,"\tSpherical Aberration: %e\n",cs1);
	fprintf(fp,"\tAngstroms per pixel: %le\n",apix);
	fprintf(fp,"\tConfidence: %e\n",confidence);
	

	fclose(fp);
		
//----------------------------------------------------------------------------
	
	return 0;
	
}

ArrayP createCTFParams( f64 defocus, f64 apix, f64 size, f64 ac, f64 kv, f64 cs ) {
		
	u32 dims[2] = {5,0};
	ArrayP ctf_params = [Array newWithType:TYPE_F64 andDimensions:dims];
	if ( ctf_params == nil ) return ctf_params;
	
	f64 * params = [ctf_params data];
	if ( params == NULL ) return ctf_params;
	
	params[0] = defocus * 1.0e-6;
	params[1] = ac;
	params[2] = getTEMLambda(kv*1000.0);
	params[3] = cs * 1.0e-3;
	params[4] = 1.0/(size*apix*1.0e-10);
	
	return ctf_params;
	
}

void ctfFromParams( ArrayP ctf_params, ArrayP curve ) {
			
	f64 * params = [ctf_params data];
	f64 * values = [curve data];
	
	if ( params == NULL || values == NULL ) return;
	
	f64 df = params[0];
	f64 ac = params[1];
	f64 lm = params[2];
	f64 cs = params[3];
	f64 ap = params[4];
	
	u32 k;
	u64 size = [curve sizeOfDimension:0];
	
	for(k=0;k<size;k++) values[k] = pow(ctf_calc(params,k),2.0);

}

void normalizeValues( f64 values[], u32 size ) {
	
	u32 r;
	f64 sum = 0;
	f64 min = values[0];
	
	for (r=0;r<size;r++) min = MIN(min,values[r]);
	for (r=0;r<size;r++) values[r] = values[r] - min;
	for (r=0;r<size;r++) sum += values[r];
	for (r=0;r<size;r++) values[r] = values[r] / sum;
	
}

u32 minPosition( f64 values[], u32 size ) {
	u32 r, min_position = 0;
	for(r=0;r<size;r++) if ( values[r] < values[min_position] ) min_position = r;
	return min_position;
}

u32 maxPosition( f64 values[], u32 size ) {
	u32 r, max_position = 0;
	for(r=0;r<size;r++) if ( values[r] > values[max_position] ) max_position = r;
	return max_position;
}

f64 detectMirrors( f64 * image, u32 rows, u32 cols, u32 ang_search, f64 ang_spacing ) {
		
	u32 rot, r, c, off = 10;

	f64 * corr_score = NEWV(f64,ang_search);
	f64 * diff_score = NEWV(f64,ang_search);
	f64 * symm_score = NEWV(f64,ang_search);
	
	f64 x_rad = cols / 2.0;
	f64 y_rad = rows / 2.0;
	
	f64 rad_2 = pow(MIN(x_rad,y_rad)-off,2);
	
	for(rot=0;rot<ang_search;rot++) {
		
		f64 cine = cos(rot*ang_spacing*RAD);
		f64 sine = sin(rot*ang_spacing*RAD);

		f64 x1, y1, rx1, ry1, rx2, ry2, y1s, y1c;
	
		for(r=1;r<rows/2;r++) {
			
			y1 = r;
			y1s = x_rad - y1*sine;
			y1c = y_rad + y1*cine;
			
			for(c=1;c<cols/2;c++) {
				
				x1 = c;
				y1 = r;
				
				f64 current_rad = x1*x1+y1*y1;
				
				if ( current_rad >= rad_2 ) continue;
			
				rx1 =  x1*cine + y1s;
				rx2 = -x1*cine + y1s;
				
				ry1 =  x1*sine + y1c;
				ry2 = -x1*sine + y1c;

				f64 p1 = interpolate2d(image,ry1,rx1,rows,cols);
				f64 p2 = interpolate2d(image,ry2,rx2,rows,cols);
						
				corr_score[rot] += p2*p1;
				diff_score[rot] += (p2-p1)*(p2-p1);	
			}			
		}
		
	}
	
	peakReduce(corr_score,ang_search,1.0,10,10);
	peakReduce(diff_score,ang_search,1.0,10,10);
	normalizeValues(corr_score,ang_search);
	normalizeValues(diff_score,ang_search);
	
	for(r=0;r<ang_search;r++) {
		u32 m1 = 90.0 / ang_spacing;
		u32 m2 = 45.0 / ang_spacing;
		f64 maxima = corr_score[r]+corr_score[(r+m1)%ang_search]+diff_score[(r+m2)%ang_search]+diff_score[(r+m1+m2)%ang_search];
		f64 minima = diff_score[r]+diff_score[(r+m1)%ang_search]+corr_score[(r+m2)%ang_search]+corr_score[(r+m1+m2)%ang_search];
		symm_score[r] = maxima / minima;
	}
	
	peakReduce(symm_score,ang_search,1.0,2,2);
	normalizeValues(symm_score,ang_search);
	
	u32 max_corr_angle = maxPosition(corr_score,ang_search);
	u32 min_corr_angle = minPosition(corr_score,ang_search);
	f64 max_corr_value = corr_score[max_corr_angle];
	f64 min_corr_value = corr_score[min_corr_angle];

	u32 max_diff_angle = maxPosition(diff_score,ang_search);
	u32 min_diff_angle = minPosition(diff_score,ang_search);
	f64 max_diff_value = diff_score[max_diff_angle];
	f64 min_diff_value = diff_score[min_diff_angle];

	u32 max_symm_angle = maxPosition(symm_score,ang_search);
	u32 min_symm_angle = minPosition(symm_score,ang_search);
	f64 max_symm_value = symm_score[max_symm_angle];
	f64 min_symm_value = symm_score[min_symm_angle];
	
	FILE * fp = fopen("/Users/craigyk/Desktop/mirror.txt","w");
	for(r=0;r<ang_search;r++) fprintf(fp,"%e %e %e\n",corr_score[r],diff_score[r],symm_score[r]);
	fclose(fp);
	
	fprintf(stderr,"Maximum correlation %e at angle: %.2f\n",max_corr_value,max_corr_angle*ang_spacing);
	fprintf(stderr,"Minimum correlation %e at angle: %.2f\n",min_corr_value,min_corr_angle*ang_spacing);
	
	fprintf(stderr,"Maximum difference %e at angle: %.2f\n",max_diff_value,max_diff_angle*ang_spacing);
	fprintf(stderr,"Minimum difference %e at angle: %.2f\n",min_diff_value,min_diff_angle*ang_spacing);
	
	fprintf(stderr,"Maximum symmetry %e at angle: %.2f\n",max_symm_value,max_symm_angle*ang_spacing);
	fprintf(stderr,"Minimum symmetry %e at angle: %.2f\n",min_symm_value,min_symm_angle*ang_spacing);
	
	return max_symm_angle*ang_spacing;
	
}

u32 peakReduce( f64 * data, s32 size, f64 sigma, s32 min_peaks, s32 max_peaks ) {
		
	s32 c_min_peaks, c_max_peaks;
	peakCount(data,size,&c_min_peaks,&c_max_peaks);
	s32 iterations = 0;
	
	while ( c_min_peaks > min_peaks && c_max_peaks > max_peaks ) {
		gaussian1d(data,0,size-1,sigma);
		peakCount(data,size,&c_min_peaks,&c_max_peaks);
		iterations++;
	}
	
	fprintf(stderr,"Reduced signal to %d min peaks and %d max peaks in %d iterations\n",c_min_peaks,c_max_peaks,iterations);
	
	return iterations;
	
}

void peakCount( f64 * data, s32 size, s32 * min_peaks, s32 * max_peaks ) {
	
	s32 i;
	*min_peaks = 0;
	*max_peaks = 0;
	for(i=0;i<size;i++) {
		s32 p1 = i - 1;
		s32 p2 = i + 1;
		if ( p1 < 0 ) p1 = size-1;
		if ( p2 >= size ) p2 = 0;
		if ( data[i] <= data[p1] && data[i] <= data[p2] ) *min_peaks = *min_peaks + 1;
		if ( data[i] >= data[p1] && data[i] >= data[p2] ) *max_peaks = *max_peaks + 1;
	}
	
}

void findDefoci( f64 * data, u32 rows, u32 cols, f64 ang, f64 defoci[] ) {
	
	u32 r, c;
	u32 off = 20;
	
	fprintf(stderr,"Finding defoci for axis %2.2f...",ang);
	
	f64 x_rad = cols / 2;
	f64 y_rad = rows / 2;
	
	f64 c1 = cos(ang*RAD);
	f64 s1 = sin(ang*RAD);
	f64 c2 = cos((ang+90)*RAD);
	f64 s2 = sin((ang+90)*RAD);
	
	u32 size = rows/2;
	
	f64 df1_v[size];
	f64 df2_v[size];

	for(r=0;r<size;r++) df1_v[r] = 0;	
	for(r=0;r<size;r++) df2_v[r] = 0;
	
	f64 x, y, rx1, rx2, ry1, ry2, p1, p2;
	
	for(r=0;r<size;r++) {
		f64 pixels = 0;
		for(c=0;c<off;c++) {
			
			x = c;
			y = r;
			
			if ( x*x+y*y >= x_rad*x_rad ) continue;
			
			rx1 =  x*c1 - y*s1 + x_rad;
			rx2 = -x*c1 - y*s1 + x_rad;
			ry1 =  y*c1 + x*s1 + y_rad;
			ry2 =  y*c1 - x*s1 + y_rad;
			
			p1 = interpolate2d(data,ry1,rx1,rows,cols);
			p2 = interpolate2d(data,ry2,rx2,rows,cols);
	
			df1_v[r] += p1+p2;
			
			rx1 =  x*c2 - y*s2 + x_rad;
			rx2 = -x*c2 - y*s2 + x_rad;
			ry1 =  y*c2 + x*s2 + y_rad;
			ry2 =  y*c2 - x*s2 + y_rad;
			
			p1 = interpolate2d(data,ry1,rx1,rows,cols);
			p2 = interpolate2d(data,ry2,rx2,rows,cols);
			
			df2_v[r] += p1+p2;
			
			pixels+=2;
			
		}
		
		df1_v[r] /= pixels;
		df2_v[r] /= pixels;
		
	}
	
	if ( peakReduce(df1_v,size,4.0,20,20) > 30 ) fprintf(stderr,"Signal along df1 is poor\n");
	if ( peakReduce(df2_v,size,4.0,20,20) > 30 ) fprintf(stderr,"Signal along df2 is poor\n");
	
	f64 * ndf1 = NEWV(f64,size);
	f64 * ndf2 = NEWV(f64,size);
	
	for(r=0;r<size;r++) ndf1[r] = df1_v[r];
	for(r=0;r<size;r++) ndf2[r] = df2_v[r];

	peakNormalize(ndf1,size);
	peakNormalize(ndf2,size);

	f64 df_f[size];
	generate1DCTF(11,size,1.55*8,2,120,df_f);
	
	peakNormalize(df_f,size);
	
	for(r=0;r<size;r++) fprintf(stdout,"%e %e %e %e\n",df1_v[r],ndf1[r],df2_v[r],ndf2[r]);
	
}

void radialGradients( f64 * data, u32 rows, u32 cols, u32 ang_search, f64 ang_spacing ) {
	
	u32 rot, r, c, off = 10;
	u32 max_rot = 90;
	
	f64 x_rad = cols / 2.0;
	f64 y_rad = rows / 2.0;
	
	f64 rad_2 = pow(MIN(x_rad,y_rad)-off,2);
	
	f64 score[ang_search][max_rot];
	f64 count[ang_search][max_rot];
	
	for(r=0;r<ang_search;r++) for(c=0;c<max_rot;c++) score[r][c] = 0.0;
	for(r=0;r<ang_search;r++) for(c=0;c<max_rot;c++) count[r][c] = 0.0;
	
	for(rot=0;rot<ang_search;rot++) {
		
		f64 cine = cos(rot*ang_spacing*RAD);
		f64 sine = sin(rot*ang_spacing*RAD);

		for(r=10;r<rows/2-off;r++) {

			f64 x = x_rad - r*sine;
			f64 y = y_rad + r*cine;
			
			f64 p1 = interpolate2d(data,y,x+3,rows,cols);
			f64 p2 = interpolate2d(data,y,x-3,rows,cols);
			f64 p3 = interpolate2d(data,y+3,x,rows,cols);
			f64 p4 = interpolate2d(data,y-3,x,rows,cols);
			
			f64 angle = (atan((p1-p2)/(p3-p4))+rot*ang_spacing*RAD)*DEG;
			if ( angle < 0 ) angle = angle + 360.0;
			if ( angle >= 360.0 ) angle = angle - 360.0;
			if ( angle >= 180.0 ) angle = 360.0 - angle;
			if ( angle >= 90.0 ) angle = 180.0 - angle;
			
//			if ( angle > 45) continue;
			
//			fprintf(stderr,"%f %f: %f %f %f %f: %f\n",x,y,p1,p2,p3,p4,angle);
			
			u32 deg = angle;
			f64 wt1 = angle - deg;
			f64 wt2 = 1.0 - wt1;
			
			f64 mag = sqrt(pow(p2-p1,2)+pow(p3-p4,2));
			
			score[rot][deg] += mag*wt2;
			score[rot][(deg+1)%max_rot] += mag*wt1;
			
			count[rot][deg] += wt2;
			count[rot][(deg+1)%max_rot] += wt1;
			
		}

	}
	
//	for(r=0;r<ang_search;r++) for(c=0;c<max_rot;c++) if (count[r][c] != 0.0 ) score[r][c] = score[r][c] / count[r][c];
	
	u32 i;
	u32 dims[3] = {max_rot,ang_search,0};
	ArrayP rot_search = [Array newWithType:TYPE_F64 andDimensions:dims];
	f64 * pix = [rot_search data];
	for(r=0,i=0;r<ang_search;r++) for(c=0;c<max_rot;c++,i++) pix[i] = score[r][c]; 
	[rot_search gaussianBlurWithSigma:1];
	normalizeValues(pix,max_rot*ang_search);
	
	u32 max_r = 0;
	for(r=0,i=0;r<ang_search;r++) for(c=0;c<max_rot;c++,i++) score[r][c] = pix[i];
	for(r=0;r<ang_search;r++) fprintf(stdout,"%f\n",score[r][0]);
	for(r=0;r<ang_search;r++) if ( score[r][0] > score[max_r][0] ) max_r = r;
	fprintf(stderr,"Maximum astig at %d\n",max_r); 
	
	if ( [rot_search writeMRCFile: "/Users/craigyk/Desktop/rot_search.mrc"] == FALSE ) fprintf(stderr,"Write Failed\n");

}

ArrayP minMaxPeakFind( ArrayP image ) {
	
	u32 i, r, c;
	u32 cols = [image sizeOfDimension:0];
	u32 rows = [image sizeOfDimension:1];
	
	ArrayP peaks = [image deepCopy];
	
	f64 * imp = [peaks data];
	f64 * imi = [image data];
	
	for(r=0,i=0;r<rows;r++) {
		for(c=0;c<cols;c++,i++) {
			imp[i] = imi[i];
			if ( r == 0 || c == 0 || r == rows-1 || c == cols-1 ) continue;
			if ( imi[i-1] < imi[i] && imi[i+1] < imi[i] && imi[i-cols] < imi[i] && imi[i+cols] < imi[i] ) imp[i] = 0;
			if ( imi[i-1] > imi[i] && imi[i+1] > imi[i] && imi[i-cols] > imi[i] && imi[i+cols] > imi[i] ) imp[i] = 1;
		}
	}
	
	return peaks;
	
}

double a_cost( const gsl_vector * variables, void * image ) {
		
	f64 * p = gsl_vector_ptr((gsl_vector *)variables,0);
	
	f64 xc = [(id)image sizeOfDimension:0]/2;
	f64 yc = [(id)image sizeOfDimension:1]/2;
	f64 ar = p[2];
	
	p[0] = ABS(p[0]);
	p[1] = ABS(p[1]);
	
	f64 xa = p[0];
	f64 ya = p[1];
	
	EllipseP ellipse = [Ellipse newAtX:xc andY:yc withXAxis:xa andYAxis:ya rotatedBy:ar];
	ArrayP advg1d = [(id)image ellipse1DAvg:ellipse];
	
	f64 cost = calcBackDrift([advg1d getRow:0],[advg1d sizeOfDimension:0],1.0,100.0);
	
//	fprintf(stderr,"Cost: %lf\n",cost);
	
	return -cost;
	
}
u32 run_minimizer( gsl_multimin_fminimizer * minimizer, u64 max_iter, f64 treshold );
void fitEllipseAstig( ArrayP image, EllipseP ellipse ) {
	
	u32 i;
	
	u32 a_ndim = 3;
	
	gsl_multimin_fminimizer * a_min = gsl_multimin_fminimizer_alloc(gsl_multimin_fminimizer_nmsimplex, a_ndim);
	gsl_vector * a_start = gsl_vector_alloc(a_ndim);
	gsl_vector * a_steps = gsl_vector_alloc(a_ndim);
	
	gsl_vector_set(a_steps,0,ABS([ellipse x_axis]*0.1));
	gsl_vector_set(a_steps,1,ABS([ellipse y_axis]*0.1));
	gsl_vector_set(a_steps,2,ABS([ellipse rotation]*0.1));
	
	gsl_vector_set(a_start,0,[ellipse x_axis]);
	gsl_vector_set(a_start,1,[ellipse y_axis]);
	gsl_vector_set(a_start,2,[ellipse rotation]);
	
	gsl_multimin_function a_function;

	a_function.n = a_ndim;
	a_function.f = &a_cost;
	a_function.params = image;
	
	gsl_multimin_fminimizer_set (a_min, &a_function, a_start, a_steps);
	u32 status = run_minimizer(a_min,100,1e-1);

	[ellipse setX_axis:gsl_vector_get(a_min->x,0)];
	[ellipse setY_axis:gsl_vector_get(a_min->x,1)];
	[ellipse setRotation:gsl_vector_get(a_min->x,2)];
	
	gsl_multimin_fminimizer_free(a_min);	
	gsl_vector_free(a_start);
	gsl_vector_free(a_steps);
	
}

ArrayP createRadialAverage( ArrayP image, EllipseP ellipse ) {
	
	ArrayP radial_avg2 = [image ellipse1DAvg:nil];
	if ( ellipse == nil ) return radial_avg2;
	
	ArrayP radial_avg1 = [image ellipse1DAvg:ellipse];	
	if ( radial_avg1 == nil ) return nil;
		
	f64 * stdv_values1 = [radial_avg1 getRow:1];
	f64 * stdv_values2 = [radial_avg2 getRow:1];
	
	f64 stdv1 = 0.0;
	f64 stdv2 = 0.0;

	u32 r, rad = MIN([radial_avg1 sizeOfDimension:0],[radial_avg2 sizeOfDimension:0]);
		
	for(r=0;r<rad;r++) stdv1 += stdv_values1[r];
	for(r=0;r<rad;r++) stdv2 += stdv_values2[r];
	
	stdv1 = stdv1 / rad;
	stdv2 = stdv2 / rad;
	
	f64 cutoff = 1.001;
		
	{
		
		f64 * avg_mean1 = [radial_avg1 getRow:0];
		f64 * avg_mean2 = [radial_avg2 getRow:0];
		f64 * avg_cont1 = [radial_avg1 getRow:1];
		f64 * avg_cont2 = [radial_avg2 getRow:1];
		
		char name[1024];
		sprintf(name,"%s.1davg.txt",basename([image name]));
		FILE * fp = fopen(name,"w");
		for (r=0;r<rad;r++) fprintf(fp,"%d\t%e\t%e\t%e\t%e\nw",r,avg_mean1[r],avg_cont1[r],avg_mean2[r],avg_cont2[r]);
		fclose(fp);
		
	}
	
	f64 back1 = calcBackDrift([radial_avg1 getRow:0],rad,1.0,100.0);
	f64 back2 = calcBackDrift([radial_avg2 getRow:0],rad,1.0,100.0);
	
	fprintf(stderr,"\n\tCalculated CTF signal for ellipse: %e, circle: %e, ratio: %e\n",back1,back2,back1/back2);
		
	if ( back1/back2 >= 0.90 ) {
		fprintf(stderr,"\tUsing Elliptical Average\n");
		[radial_avg2 release];
		return radial_avg1;
	} else {
		fprintf(stderr,"\tUsing Circular Average\n");
		[ellipse setX_axis:[ellipse y_axis]];
		[radial_avg1 release];
		return radial_avg2;
	}
	
}

f64 calcBackDrift( f64 values[], u32 rad, f64 mins, f64 maxs ) {
	
	f64 * temp = NEWV(f64,rad);
	
	f64 kfac = sqrt(4);
	
	u32 r, k;
	
	f64 back_drift = 0.0;
	f64 sigma = mins;
	
	while ( sigma < maxs ) {
		memcpy(temp,values,sizeof(f64)*rad);
		gaussian1d(temp,0,rad-1,sigma);
		f64 oldsize = back_drift;
		for(r=rad*0.05;r<rad-1;r++) if ( temp[r] < temp[r+1] ) back_drift += temp[r+1] - temp[r];
		if ( back_drift == oldsize ) break;
		sigma *= kfac;
	}
	
	free(temp);
	return back_drift;
	
}

void generate1DCTF( f64 df, u32 size, f64 apix, f64 cs, f64 kv, f64 dfs[] ) {
	
	u32 r;
	df = df * 1.0e-6;
	apix = apix * 1.0e-10;
	cs = cs * 1.0e-3;
	
	f64 lambda = getTEMLambda(kv*1000.0);
	
	f64 x_freq = 0.5/(size*apix);
	
	f64 a1 = 0.07;
	f64 a2 = sqrt(1.0-pow(a1,2.0));
	
	for(r=0;r<size;r++) {
		f64 x = r*x_freq;
		f64 f = x*x;
		f64 chi = lambda*PI*f*(df-0.5*lambda*lambda*f*cs);
		f64 z = a2*sin(chi)+a1*cos(chi);
		dfs[r] = z*z;
	}
	
}
