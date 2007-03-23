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
	
	int i, j, k;
	float minSize = 10000, maxSize = 1.0, minPeriod = 0.1, minStable = 0.1;

	PStack im2Regions = NewPStack(100);

	Image im2 = ReadPGMFile(argv[1]);
	Image out = ConvertImage1(CopyImage(im2));
	fprintf(stderr,"Read in image %s with dimensions %d %d\n",argv[1],im2->rows,im2->cols);
	FindMSERegions(im2,im2Regions,minSize,maxSize,1,2,FALSE,TRUE);

	PStack dc = NewPStack(10);
	
	for(i=0;i<im2Regions->stacksize;i++) {
		Region re = im2Regions->items[i];
		float area = PolygonArea(re->border);
		float numberOfSections = area / 44000;
		if ( numberOfSections >= 1 && numberOfSections < 5 ) {
			PolygonACD(re->border,0.06,dc);
		}
	}
	
	Region cc = im2Regions->items[i];
	//DrawPolygon(cc->border,out,PIX3(0,255,0));
	for(i=0;i<dc->stacksize;i++) {
		Polygon border = dc->items[i];
		int area = PolygonArea(border);
		if ( area < 44000 || area > 44000 * 1.6 ) continue;
		PolygonVertexEvolution(border,4);
		int color = RandomColor(150);
		for(j=0;j<border->numberOfVertices;j++) {
			Ellipse e = NewEllipse(border->vertices[j].x,border->vertices[j].y,5,5,0);
			DrawEllipse(e,out,color); free(e);
		}
		DrawPolygon(border,out,color);
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


