#include "cvtypes.h"
#include "Array.h"
#include "MRC.h"
#include "PGM.h"
#include "Image.h"
#import "Ellipse.h"
#include "util.h"
#include "getopts.h"
#include "ctf.h"
#include "geometry.h"
#include <gsl/gsl_math.h>
#include <gsl/gsl_linalg.h>
#include <gsl/gsl_blas.h>
#include <gsl/gsl_eigen.h>
#include <gsl/gsl_multimin.h>

ArrayP createRadialAverage( ArrayP image, EllipseP ellipse );
EllipseP ellipseRANSAC( ArrayP edges, f64 fit_treshold, f64 min_percent_inliers, f64 certainty_probability, u64 max_iterations );
void generateBoundEllipses( f64 e[], f64 b1[], f64 b2[], f64 treshold );
void ellipseNorm( f64 e[], f64 TR[3][3] );
f64 ellipseCircumference( f64 e[] );

int main (int argc, char **argv) {
	
	srand((unsigned)time(NULL));
	
	u32 dims[3] = { 1024, 1024, 0 };
	ArrayP testimage = [Array newWithType:TYPE_F64 andDimensions:dims];
	
	u32 i, size = [testimage numberOfElements];
	f64 * v = [testimage data];

	for(i=0;i<size;i++) v[i] = 10.0;
	
	f64 x_c = 1024/2 + 0.5;
	f64 y_c = 1024/2 - 0.5;
	
	f64 x_a = 1.1;
	
	EllipseP e1 = [Ellipse newAtX:x_c andY:y_c withXAxis:100 andYAxis:100*1.5 rotatedBy:45*RAD];
	EllipseP e2 = [Ellipse newAtX:x_c andY:y_c withXAxis:150 andYAxis:150*1.5 rotatedBy:45*RAD];
	EllipseP e3 = [Ellipse newAtX:x_c andY:y_c withXAxis:200 andYAxis:200*1.5 rotatedBy:45*RAD];
	EllipseP e4 = [Ellipse newAtX:x_c andY:y_c withXAxis:200 andYAxis:300 rotatedBy:-25*RAD];
	
	[e1 toGeneralConic];
	[e1 toGeneralEllipse];
	[e2 toGeneralConic];
	[e3 toGeneralEllipse];
	[e3 toGeneralConic];
	
	[e1 drawInArray:testimage];
	[e2 drawInArray:testimage];
	[e3 drawInArray:testimage];
	
	f64 max = MAX_F64(v,size);
	f64 min = MIN_F64(v,size);
	
	for(i=0;i<size;i++) v[i] = v[i] + randomNumber(min,max*2);
	
	ArrayP te1 = [testimage deepCopy];
	ArrayP te2 = [testimage deepCopy];
	
	[te1 gaussianBlurFFTWithSigma:10];
	[te2 gaussianBlurWithSigma:10];
	
	[te1 writeMRCFile:"te1.mrc"];
	[te2 writeMRCFile:"te2.mrc"];
	[testimage writeMRCFile:"te3.mrc"];
	
	f64 edge_maxt = 0.9;
	f64 edge_mint = edge_maxt*0.1;
	u32 edge_count = cannyedges2d([te2 data],[te2 sizeOfDimension:1],[te2 sizeOfDimension:0],edge_mint,edge_maxt,5.0);
	
	fprintf(stderr,"Found %d edges!!\n",edge_count);
	
	f64 fit_treshold = 0.5;
	f64 min_percent = 0.001;
	f64 fit_percent = 0.99;
	f64 max_iterations = 100000;
	EllipseP e5 = ellipseRANSAC(te2,fit_treshold,min_percent,fit_percent,max_iterations);	
	
	ArrayP image_copy = [testimage deepCopy];
	[image_copy gaussianBlurWithSigma:10];
	[image_copy scaleFrom:0.0 to:1.0];
	[e5 drawInArray:image_copy];
	[te2 scaleFrom:0.0 to:2.0];
	[te2 addImage:image_copy];
	[te2 writeMRCFile:"te4.mrc"];
	[image_copy release];

	ArrayP avg1d = [testimage ellipse1DAvg:e5];
	
	u32 a_size = [avg1d sizeOfDimension:0];
	f64 * avg = [avg1d getRow:0];
	f64 * dev = [avg1d getRow:1];
	f64 * cnt = [avg1d getRow:2];
	
	FILE * fp = fopen("test.txt","w");
	for(i=0;i<a_size;i++) fprintf(fp,"%e\t%e\t%e\n",avg[i],dev[i],cnt[i]);
	fclose(fp);
	
}

ArrayP createRadialAverage( ArrayP image, EllipseP ellipse ) {
	
	ArrayP radial_avg2 = [image ellipse1DAvg:nil];
	if ( ellipse == nil ) return radial_avg2;
	
	ArrayP radial_avg1 = [image ellipse1DAvg:ellipse];	
	if ( radial_avg1 == nil ) return nil;
	
	f64 * avg_values1 = [radial_avg1 getRow:0];
	f64 * avg_values2 = [radial_avg2 getRow:0];
	f64 * stdv_values1 = [radial_avg1 getRow:1];
	f64 * stdv_values2 = [radial_avg2 getRow:1];
	
	f64 stdv1 = 0.0;
	f64 stdv2 = 0.0;

	u32 r, rad = MIN([radial_avg1 sizeOfDimension:0],[radial_avg2 sizeOfDimension:0]);
	
	f64 * stdv_weights = NEWV(f64,rad);
	
	f64 sum_weight = 0.0;
	for(r=0;r<rad;r++) stdv_weights[r] = ABS(avg_values1[r]-avg_values2[r]);
	for(r=0;r<rad;r++) sum_weight += stdv_weights[r];
	for(r=0;r<rad;r++) stdv_weights[r] = stdv_weights[r] / sum_weight;
		
	for(r=0;r<rad;r++) stdv1 += sqrt(stdv_values1[r])*stdv_weights[r];
	for(r=0;r<rad;r++) stdv2 += sqrt(stdv_values2[r])*stdv_weights[r];
	
	stdv1 = stdv1 / rad;
	stdv2 = stdv2 / rad;
	
	f64 cutoff = 1.001;
	
	{
		
		f64 * avg_mean1 = [radial_avg1 getRow:0];
		f64 * avg_mean2 = [radial_avg2 getRow:0];
		f64 * avg_stdv1 = [radial_avg1 getRow:1];
		f64 * avg_stdv2 = [radial_avg2 getRow:1];
		f64 * avg_cont1 = [radial_avg1 getRow:2];
		f64 * avg_cont2 = [radial_avg2 getRow:2];
		
		char name[1024];
		sprintf(name,"%s-1davg.txt",basename([image name]));
		FILE * fp = fopen(name,"w");
		for (r=0;r<rad;r++) fprintf(fp,"%d\t%e\t%e\t%e\t%e\t%e\t%e\nw",r,avg_mean1[r],avg_stdv1[r],avg_cont1[r],avg_mean2[r],avg_stdv2[r],avg_cont2[r]);
		fclose(fp);
		
	}
	
	if ( stdv2/stdv1 > cutoff ) {
		fprintf(stderr,"\n\tUsing Elliptical Average\n\tstdv:stdv (%e:%e) %.4f > %.3f\n",stdv2,stdv1,stdv2/stdv1,cutoff);
		[radial_avg2 release];
		return radial_avg1;
	} else {
		fprintf(stderr,"\n\tUsing Circular Average\n\tstdv:stdv (%e:%e) %.4f < %.3f\n",stdv2,stdv1,stdv2/stdv1,cutoff);
		[ellipse setX_axis:[ellipse y_axis]];
		[radial_avg1 release];
		return radial_avg2;
	}
	
}

