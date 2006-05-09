#include "defs.h"

/*----------------------------------------------------------------------*/

Region NewRegion( Ellipse e, Image image, PointStack sizes, PointStack border, int stable, int root ) {

	if ( e == NULL ) return NULL;
	
	Region reg = malloc(sizeof(struct RegionSt));
	if ( reg == NULL ) return NULL;
	
	reg->root   = root;
	reg->stable = stable;
	reg->border = CopyPointStack(border);
	reg->sizes  = CopyPointStack(sizes);
	
	reg->image = image;
	reg->row = e->erow;
	reg->col = e->ecol;
	reg->maj = e->majaxis;
	reg->min = e->minaxis;
	reg->phi = e->phi;
	reg->ori = e->phi*DEG;
	reg->A = e->A;
	reg->B = e->B;
	reg->C = e->C;
	reg->D = e->D;
	reg->E = e->E;
	reg->F = e->F;
	reg->minr = e->minr;
	reg->maxr = e->maxr;
	reg->minc = e->minc;
	reg->maxc = e->maxc;
	
	return reg;
	
}
	
void GenerateGradientOrientationBins( Region key, Image im, float *bins ) {

	int row, col, i;
	static double **IT = NULL;
	static Image patch;
	static float *kernel;
	int wrad = 20;
	int maxd = wrad*2;
	if ( IT == NULL ) {
		patch = CreateImage(maxd+1,maxd+1);
		int ksize = wrad+1;
		kernel = malloc(ksize*sizeof(float));
		float sigma = 30;
		float sigma2sq = sigma*sigma*2;
		float norm = 1.0/(sqrt(2*PI)*sigma);
		for (i=0;i<ksize;i++) { kernel[i] = exp(-(i*i)/sigma2sq)*norm;}
		IT = AllocDMatrix(3,3,0,0);
	}

	struct EllipseSt e1, e2;
	e1.phi = key->phi;
	e1.erow = key->row; e1.ecol = key->col;
	e1.majaxis = key->maj; e1.minaxis = key->min;
	e2.phi = key->phi;
	e2.erow = wrad, e2.ecol = wrad;
	e2.minaxis = wrad; e2.majaxis = wrad;
	
	ComputeEllipseTransform(&e1,&e2,NULL,IT);
	AffineTransformImage( im, patch, NULL, IT );
	
	int mag = 0, ang = 0;
	float vmag =0, hmag = 0;

	int **p1 = patch->pixels;
	for (row=1;row<maxd;row++) {
		for (col=1;col<maxd;col++) {
			int rad  = sqrt((row-wrad)*(row-wrad)+(col-wrad)*(col-wrad));
			if ( rad > wrad ) continue;
			int a = p1[row][col+1];
			int b = p1[row][col-1];
			int c = p1[row-1][col];
			int d = p1[row+1][col];
			if ( a<0||b<0||c<0||d<0 ) continue;
			vmag = c-d;
			hmag = a-b;
			mag = sqrt(vmag*vmag+hmag*hmag);
			ang = atan2(vmag,hmag)*DEG; if ( ang < 0 ) ang += 360;
			bins[ang] += mag*kernel[rad];
	}}
	
	
	
}

void DetermineMajorGradientOrientations( Region key, FStack orientations ) {
	
	if ( key == NULL || key->image == NULL || orientations == NULL ) return;

	int i, k;
	float *bins = malloc(sizeof(float)*360), largest;
	
	for (i=0;i<360;i++) bins[i] = 0.0;
	GenerateGradientOrientationBins(key,key->image,bins);
	WrapGaussianBlur1D(bins,0,359,5);
	largest = LargestValue(bins,0,359)*0.9;
	for (i=0;i<360&&bins[i]>largest;i++);
	while (i<360) {
		k=i;
		while ( bins[k%360] > largest ) k++;
		if ( k != i ) PushFStack(orientations,((i+k)/2)%360);
		i=k+1;
	}
	
	free(bins);
	
}

void RegionsToDescriptors( PStack regions, PStack descriptors, int o1, int o2, int o3, int o4, int d1, int pb, int ob, int d2 ) {
	if ( regions == NULL || descriptors == NULL ) return;
	Image patch = CreateImage(41,41);
	FStack orientations = NewFStack(15);
	int k;
	for (k=0;k<regions->stacksize;k++) {
		Region key = regions->items[k];
		DetermineMajorGradientOrientations(key,orientations);
		while ( !FStackEmpty(orientations) ) {
			key->ori = PopFStack(orientations);
			RegionToPatch( key, patch );
			PushPStack(descriptors,NewDescriptor(key,36,1,CreatePCADescriptor(patch)));
		}
	}
	FreeImage(patch);
}

void RegionToPatch( Region key, Image patch ) {
	if ( key == NULL || patch == NULL ) return;
	struct EllipseSt e1, e2;
	double **IT = AllocDMatrix(3,3,0,0);
	double **TR = AllocDMatrix(3,3,0,0);
	int desrad = (patch->rows-1)/2;
	e1.majaxis = key->maj; e1.minaxis = key->min;
	e1.erow = key->row; e1.ecol = key->col;
	e1.phi = key->phi;
	e2.majaxis = desrad; e2.minaxis = desrad;
	e2.erow = desrad; e2.ecol = desrad;
	e2.phi = key->phi-key->ori*RAD;
	ComputeEllipseTransform(&e1,&e2,TR,IT);
	AffineTransformImage(key->image,patch,TR,IT);
	FreeDMatrix(IT,0,0);
	FreeDMatrix(TR,0,0);
}

Descriptor NewDescriptor( Region key, int dlength, char dtype, float *d ) {
	if ( key == NULL || d == NULL ) return NULL;
	Descriptor des = malloc(sizeof(struct DescriptorSt));
	if ( des == NULL ) return NULL;
	des->descriptortype = dtype;
	des->descriptorlength = dlength;
	des->row = key->row;
	des->col = key->col;
	des->ori = key->phi-key->ori*RAD;
	des->descriptor = d;
	return des;
}

float *CreateSIFTDescriptor( Image patch, int pb, int ob ) {
	
	if ( patch == NULL ) return NULL;

	int row, col, k;
	float des[pb][pb][ob];
	for (row=0;row<pb;row++) for (col=0;col<pb;col++) for (k=0;k<ob;k++) des[row][col][k] = 0;
	
	int desrad = 20;
	float binrat = (float)ob/360.0;
	float bincet = 360/(2*ob);
	float sizrat = (float)pb/(desrad*2);

	int **p1 = patch->pixels;
	
	int ksize = sqrt(desrad*desrad*2)+0.5;
	float *gkernel = malloc(ksize*sizeof(float));
	float sigma = 10;
	float sigma2sq = sigma*sigma*2;
	float norm = 1.0/(sqrt(2*PI)*sigma);
	for (k=0;k<ksize;k++) { gkernel[k] = exp(-(k*k)/sigma2sq)*norm;}
	
	for (row=1;row<desrad*2;row++) {
		for (col=1;col<desrad*2;col++) {
			int a = p1[row][col+1];
			int b = p1[row][col-1];
			int c = p1[row-1][col];
			int d = p1[row+1][col];
			if ( a<0||b<0||c<0||d<0 ) continue;
			int vmag = c-d;
			int hmag = a-b;
			float ang = atan2(vmag,hmag)*DEG-bincet;
			int rad = sqrt((row-desrad)*(row-desrad)+(col-desrad)*(col-desrad));
			int mag = sqrt(hmag*hmag+vmag*vmag)*gkernel[rad];   
			if ( ang < 0 ) ang += 360;
			ang *= binrat;
			float orow = row*sizrat-0.5;
			float ocol = col*sizrat-0.5;
			int ridx, cidx;
			if ( orow < 0 ) ridx = orow-1;
			else ridx = orow;
			if ( ocol < 0 ) cidx = ocol-1;
			else cidx = ocol;
			int didx1 = ang;
			int didx2 = (didx1+1)%ob;
			float rwgt1 = 1 - orow + ridx;
			float rwgt2 = 1 - rwgt1;
			float cwgt1 = 1 - ocol + cidx;
			float cwgt2 = 1 - cwgt1;
			float dwgt1 = 1 - ang + didx1;
			float dwgt2 = 1 - dwgt1;
			if (ridx>=0&&ridx<pb&&cidx>=0&&cidx<pb) {
				des[ridx][cidx][didx1] += mag*rwgt1*cwgt1*dwgt1;
				des[ridx][cidx][didx2] += mag*rwgt1*cwgt1*dwgt2;
			} ridx++;
			if (ridx>=0&&ridx<pb&&cidx>=0&&cidx<pb) {
				des[ridx][cidx][didx1] += mag*rwgt2*cwgt1*dwgt1;
				des[ridx][cidx][didx2] += mag*rwgt2*cwgt1*dwgt2;
			} cidx++;
			if (ridx>=0&&ridx<pb&&cidx>=0&&cidx<pb) {
				des[ridx][cidx][didx1] += mag*rwgt2*cwgt2*dwgt1;
				des[ridx][cidx][didx2] += mag*rwgt2*cwgt2*dwgt2;
			} ridx--;
			if (ridx>=0&&ridx<pb&&cidx>=0&&cidx<pb) {
				des[ridx][cidx][didx1] += mag*rwgt1*cwgt2*dwgt1;
				des[ridx][cidx][didx2] += mag*rwgt1*cwgt2*dwgt2;
			}
		}
	}
	
	int j = 0;
	int desize = pb*pb*ob;
	float *de = malloc(sizeof(float)*desize);
	if (de == NULL) return NULL;
	for (row=0;row<pb;row++) {
		for (col=0;col<pb;col++) {
			for (k=0;k<ob;k++) {
				de[j++] = des[row][col][k];
	}}}
	float l = 0, s = 1000000;
	for(k=0;k<desize;k++) de[k] = MIN(de[k],1000000);
	for(k=0;k<desize;k++) {
		s = MIN(s,de[k]);
		l = MAX(l,de[k]);
	}
	for(k=0;k<desize;k++) de[k] = (de[k]-s)*(255.0/(l-s));
		
	return de;

}

float *CreatePCADescriptor( Image patch ) {
	
	#define PatchSize  41
	#define PatchLength (PatchSize * PatchSize)
	#define GPLEN ((PatchSize - 2) * (PatchSize - 2) * 2)
	#define PCALEN 36
	#define EPCALEN 36 
	#define PatchMag 20

	float *kv = malloc(sizeof(float)*PatchLength*2);
	
	int i, j;
	static float *avgs= NULL, **eigs;
	if ( avgs == NULL ) {
		float val;
		FILE *pcaf = fopen("pcavects.txt", "rb");
		avgs = malloc(sizeof(float)*GPLEN);
		eigs = AllocFMatrix(EPCALEN,GPLEN,0,0);
		for (i=0;i<GPLEN;++i) {
			if (fscanf(pcaf, "%f", &val) != 1) FatalError("Invalid PCA Vector File.\n");
			avgs[i] = (float)val;
		}
		for (i=0;i<GPLEN;++i) {
			for (j=0;j<PCALEN;j++) {
				if (fscanf(pcaf,"%f", &val) != 1) FatalError("Invalid PCA Vector File.\n");
				if (j<EPCALEN) eigs[j][i] = (float)val;
			}
		}
		fclose(pcaf);
	}
		
	int count=0, **p1 = patch->pixels, row, col;
	for (row=1;row<PatchSize-1;++row) {
		for (col=1;col<PatchSize-1;++col) {	
			int a = p1[row][col+1];
			int b = p1[row][col-1];
			int c = p1[row-1][col];
			int d = p1[row+1][col];
			if ( a<0||b<0||c<0||d<0 ) {
				kv[count]   = 0;
				kv[count+1] = 0;
			} else {	
				kv[count]   = a-b;
				kv[count+1] = c-d;
			}
			count += 2;	
		}
	}
	
	float *kpdescriptor = malloc(sizeof(float)*EPCALEN);
	for (count=0;count<GPLEN;++count) kv[count] -= avgs[count];
	for (count=0;count<EPCALEN;++count) {
		kpdescriptor[count] = 0;
		for (row=0;row<GPLEN;++row) kpdescriptor[count] += eigs[count][row]*kv[row];
	}
	
	return kpdescriptor;
	
}

void PrintSIFTDescriptors( char *name, PStack descriptors ) {
	
	FILE *fp = fopen( name, "w" );
	if ( fp == NULL ) return;
	
	int k;
	for(k=0;k<descriptors->stacksize;k++) {
		Descriptor d = descriptors->items[k];
		fprintf(fp,"%f %f ",d->row,d->col);
		int i; for(i=0;i<d->descriptorlength;i++) fprintf(fp,"%f ",d->descriptor[i]);fprintf(fp,"\n");
	}
	
	fclose(fp);
	
}

void PrintRegions( char *name, PStack Regions ) {
	FILE *fp = fopen(name,"w");
	if ( fp == NULL ) return;
	int k;
	fprintf(fp,"1.0\n%d\n",Regions->stacksize);
	for(k=0;k<Regions->stacksize;k++) {
		Region key = Regions->items[k];
		float A = 1.0/(key->min*key->min);
		float C = 1.0/(key->maj*key->maj);
		float sine = sin(key->phi);
		float cose = cos(key->phi);
		float A1 = A*cose*cose+C*sine*sine;
		float B1 = C*sine*cose-A*sine*cose;
		float C1 = A*sine*sine+C*cose*cose;
		printf("%f %f %f %f %f\n",key->col,key->row,A1,B1,C1);
	}
	fclose(fp);
}
