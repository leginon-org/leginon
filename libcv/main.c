#include "geometry.h"
#include "util.h"
#include "image.h"
#include "mser.h"
#include "csift.h"
#include "match.h"
#include "lautil.h"
#include "geometry.h"
#include "mutil.h"

int main (int argc, char **argv) {
	
	srand(time(NULL));
	libCV_debug = 0;
	
	int i, j, k;
	float minSize = 5000, maxSize = 1.0, minPeriod = 0.1, minStable = 0.1;

	PStack im1Regions = NewPStack(100);
	PStack im2Regions = NewPStack(100);

	float t0 = CPUTIME;
	
	Image im1 = ReadPGMFile(argv[1]);
	Image im2 = ReadPGMFile(argv[2]);
	Image out = ConvertImage1(CopyImage(im2));
		
	FindMSERegions(im2,im2Regions,minSize,maxSize,minPeriod,minStable);
	FindMSERegions(im1,im1Regions,minSize,maxSize,minPeriod,minStable);
	
	float maxArea = 0; Polygon template = NULL, search = NULL, current = NULL;
	for(i=0;i<im1Regions->stacksize;i++) {
		Region re = im1Regions->items[i];
		float ellipseArea = PolygonArea(re->border);
		int numberOfSections = ellipseArea / 44000;
		if ( numberOfSections >= 1 && numberOfSections < 2 ) {
			fprintf(stderr,"Found %d sections with size %f.\n",numberOfSections,ellipseArea);
			current = re->border;
			for(k=0;k<im1Regions->stacksize;k++) {
				re = im1Regions->items[k];
				if ( !PointInPolygon(current,re->row,re->col) ) continue;
				ellipseArea = ( re->maj * re->min * PI ) / 48361;
				if ( ellipseArea < 0.8 && maxArea < ellipseArea ) maxArea = ellipseArea;
			}
		}
	}
	
	WritePPM("sections.ppm",out);
	
	PStack dc = NewPStack(10);
	
	for(i=0;i<im2Regions->stacksize;i++) {
		Region re = im2Regions->items[i];
		float ellipseArea = PolygonArea(re->border);
		int numberOfSections = ellipseArea / 44000 + 0.5;
		if ( numberOfSections >= 1 && numberOfSections < 5 ) {
			if ( ABS(re->maj-148) > 5 && ABS(re->min-148) > 5 ) continue;
			fprintf(stderr,"Found %d sections.\n",numberOfSections);
			DrawPolygon(re->border,out,PIX3(255,0,0));
			PolygonACD(re->border,2,0.1,1.0,dc);
		}
	}
	
	WritePPM("sections.ppm",out);
	
	//RegionsToSIFTDescriptors(im1Regions,im1Descriptors,4,8,41);
	//fprintf(stderr,"Created %d descriptors from %d regions in %2.2f seconds\n",im1Descriptors->stacksize,im1Regions->stacksize,CPUTIME-t0);
	//PrintSIFTDescriptors("csift1",im1Descriptors);
	
	
	
	/*
	PStack im2Regions = NewPStack(100);
	PStack im2Descriptors = NewPStack(100);
	
	t0 = CPUTIME;
	
	Image im2 = ReadPGMFile(argv[2]);
	FindMSERegions(im2,im2Regions,minSize,maxSize,minPeriod,minStable);
	RegionsToSIFTDescriptors(im2Regions,im2Descriptors,4,8,41);
	fprintf(stderr,"Created %d descriptors from %d regions in %2.2f seconds\n",im2Descriptors->stacksize,im2Regions->stacksize,CPUTIME-t0);
	
	PStack matches = NewPStack(100);
	double **transform = AllocDMatrix(3,3,0,0);
	FindMatches(im1Descriptors,im2Descriptors,matches,10);
	fprintf(stderr,"Found %d initial matches.\n",matches->stacksize);
	ScreenMatches(matches,transform);
	fprintf(stderr,"A1 = [ ");
	for(k=0;k<3;k++)fprintf(stderr,"%f %f %f;",transform[k][0],transform[k][1],transform[k][2]);
	fprintf(stderr,"]\n");
	
	Image im3 = CreateImage(im1->rows,im1->cols);
	
	AffineTransformImage(im2,im3,NULL,transform);
	
	for (i=0;i<im1->rows;i++) {
		for (j=0;j<im1->cols;j++) {
			int rv = MAX(0,im1->pixels[i][j]);
			int bv = MAX(0,im3->pixels[i][j]);
			im3->pixels[i][j] = PIX3(rv,0,bv);
	}}
	
	WritePPM("affine.ppm",im3);
	*/
	return 0;
	
}


