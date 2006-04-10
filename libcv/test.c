#include "defs.h"

int main (int argc, char **argv) {
	float t0=CPUTIME;
	fprintf(stderr,"Creating Descriptors for image %s:\n", argv[1]);
	PStack k1 = NewPStack(100);
	PStack d1 = NewPStack(100);
	Image im1 = ReadPGMFile(argv[1]);
	CreateMSERKeypoints(im1,k1,40,im1->rows*im1->cols*0.9,5,0.02);
	//KeypointsToDescriptors(k1,d1,TRUE,FALSE,FALSE,TRUE,TRUE,4,8,FALSE);
	fprintf(stderr,"Total time: %f  Regions: %d  Descriptors: %d\n", CPUTIME-t0,k1->stacksize,d1->stacksize);
	//PrintSIFTDescriptors("1.csift",d1);

	t0=CPUTIME;
	fprintf(stderr,"Creating Descriptors for image %s:\n", argv[2]);
	PStack k2 = NewPStack(100);
	PStack d2 = NewPStack(100);
	Image im2 = ReadPGMFile(argv[2]);
	CreateMSERKeypoints(im2,k2,40,im2->rows*im2->cols*0.9,5,0.02);
	//KeypointsToDescriptors(k2,d2,TRUE,FALSE,FALSE,TRUE,TRUE,4,8,FALSE);
	fprintf(stderr,"Total time: %f  Regions: %d  Descriptors: %d\n", CPUTIME-t0,k2->stacksize,d2->stacksize);
	//PrintSIFTDescriptors("2.csift",d2);
	
	PStack ma = NewPStack(100);
	double **transform = AllocDMatrix(3,3,0,0);
	FindMatches(d1,d2,ma,40);
	ScreenMatches(ma,transform);
	fprintf(stderr,"A1 = [ ");
	int k; for(k=0;k<3;k++)fprintf(stderr,"%f %f %f;",transform[k][0],transform[k][1],transform[k][2]);
	fprintf(stderr,"]\n");
	
	while(!PStackEmpty(k1)) {
		Keypoint key = PopPStack(k1);
		free(key);
	} FreePStack(k1);
	while(!PStackEmpty(k2)) {
		Keypoint key = PopPStack(k2);
		free(key);
	} FreePStack(k2);
	while(!PStackEmpty(d1)) {
		Descriptor d = PopPStack(d1);
		free(d->descriptor);
		free(d);
	} FreePStack(d1);
	while(!PStackEmpty(d2)) {
		Descriptor d = PopPStack(d2);
		free(d->descriptor);
		free(d);
	} FreePStack(d2);
	while(!PStackEmpty(ma)) {
		Match m = PopPStack(ma);
		free(m);
	} FreePStack(ma);
	free(im1->pixels[0]);
	free(im1->pixels);
	free(im1);
	free(im2->pixels[0]);
	free(im2->pixels);
	free(im2);

	return 0;
}
