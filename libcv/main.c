#include "defs.h"

int main (int argc, char **argv) {
	
	float t0=CPUTIME;
	int k;
	
	t0 = CPUTIME;
	fprintf(stderr,"Creating Descriptors for image %s:\n", argv[1]);
	PStack k1 = NewPStack(100);
	PStack d1 = NewPStack(100);
	Image im1 = ReadPGMFile(argv[1]);
	EnhanceImage(im1,0,255,0.01,0.01);
	FindMSERegions(im1,k1,0.00004,1.0,0.03,0.05);
	RegionsToDescriptors(k1,d1,TRUE,FALSE,FALSE,TRUE,TRUE,4,8,FALSE);
	fprintf(stderr,"Total time: %f  Regions: %d  Descriptors: %d\n", CPUTIME-t0,k1->stacksize,d1->stacksize);
	PrintSIFTDescriptors("1.csift",d1);
	
	t0=CPUTIME;
	fprintf(stderr,"Creating Descriptors for image %s:\n", argv[2]);
	PStack k2 = NewPStack(100);
	PStack d2 = NewPStack(100);
	Image im2 = ReadPGMFile(argv[2]);
	FindMSERegions(im2,k2,0.00004,1.0,0.03,0.05);
	RegionsToDescriptors(k2,d2,TRUE,FALSE,FALSE,TRUE,TRUE,4,8,FALSE);
	fprintf(stderr,"Total time: %f  Regions: %d  Descriptors: %d\n", CPUTIME-t0,k2->stacksize,d2->stacksize);
	PrintSIFTDescriptors("2.csift",d2);
	
	PStack ma = NewPStack(100);
	double **transform = AllocDMatrix(3,3,0,0);
	FindMatches(d1,d2,ma,30);
	fprintf(stderr,"Found %d initial matches.\n",ma->stacksize);
	ScreenMatches(ma,transform);
	fprintf(stderr,"A1 = [ ");
	for(k=0;k<3;k++)fprintf(stderr,"%f %f %f;",transform[k][0],transform[k][1],transform[k][2]);
	fprintf(stderr,"]\n");

	return 0;
	
}


