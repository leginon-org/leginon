#include "csift.h"
#include "geometry.h"
#include "pcavects.h"

FVec GenerateOrientationHistogram( Image patch );
void FindDominantOrientations( FVec hist, float peak, FStack orientations );
void DeterminePatchOrientations( Image patch, FStack orientations );

void DeterminePatchOrientations( Image patch, FStack orientations ) {

	FVec hist = GenerateOrientationHistogram(patch);
	if ( hist == NULL ) return;
	WrapGaussianBlur1D(hist->values,hist->l,hist->r,10);
	FindDominantOrientations(hist,0.9,orientations);
	FVecFree(hist);
	
}

FVec GenerateOrientationHistogram( Image patch ) {
	
	if ( !ImageIsGood(patch) ) return NULL;
	
	int i, r, c;
	FVec hist = FVecNew(0,359);
	for (i=0;i<=359;i++) hist->values[i] = 0.0;
	
	int maxRow = patch->rows;
	int maxCol = patch->cols;
		
	for (r=1;r<maxRow-1;r++) {
		for (c=1;c<maxCol-1;c++) {
			int v1 = patch->pixels[r-1][c];
			int v2 = patch->pixels[r+1][c];
			int v3 = patch->pixels[r][c+1];
			int v4 = patch->pixels[r][c-1];
			if ( v1 < 0 || v2 < 0 || v3 < 0 || v4 < 0 ) continue;
			int vmag = v1 - v2;
			int hmag = v3 - v4;
			int mag = sqrt(hmag*hmag+vmag*vmag);
			int ori = atan2(vmag,hmag)*DEG + 0.5;
			if ( ori < 0 ) ori += 360;
			hist->values[ori] += mag;
		}
	}

	return hist;
	
}

void FindDominantOrientations( FVec hist, float peak, FStack orientations ) {
	
	int i, k;
	
	float largest = LargestValue(hist->values,hist->l,hist->r)*peak;
	
	for (i=hist->l; i<=hist->r && hist->values[i]>largest; i++);
	
	while (i<360) {
		k=i;
		while ( hist->values[k%360] > largest ) k++;
		if ( k != i ) PushFStack(orientations,((i+k)/2)%360);
		i=k+1;
	}
	
}

void RotateImage( Image im1, Image im2, float angle );

void RegionsToSIFTDescriptors( PStack regions, PStack descriptors, int pb, int ob, int psize ) {
	
	if ( regions == NULL || descriptors == NULL ) return;
	
	if ( psize % 2 == 0 ) psize++;
	Image patch = CreateImage(psize*sqrt(2),psize*sqrt(2));
	Image rpatch = CreateImage(psize,psize);
	FStack orientations = NewFStack(15);
	
	int k;
	
	for (k=0;k<regions->stacksize;k++) {
		Region region = regions->items[k];
		RegionToPatch(region,region->image,patch,6.0);
		DeterminePatchOrientations(patch,orientations);
		while ( !FStackEmpty(orientations) ) {
			float orientation = PopFStack(orientations);
			RotateImage(patch,rpatch,orientation);
			float *newDescriptor = PCADescriptorFromPatch(rpatch);
			PushPStack(descriptors,NewDescriptor(region,36,3,newDescriptor));
		}
	}
	
	FreeImage(patch); FreeImage(rpatch);

}

void RotateImage( Image im1, Image im2, float angle ) {
	int Xc1 = im1->rows * 0.5;
	int Yc1 = im1->cols * 0.5;
	int Xc2 = im2->rows * 0.5;
	int Yc2 = im2->cols * 0.5;
	Ellipse e1 = NewEllipse(Xc1,Yc1,Xc1,Yc1,angle*RAD);
	Ellipse e2 = NewEllipse(Xc2,Yc2,Xc2+1,Yc2+1,0);
	double **IT = AllocDMatrix(3,3,0,0);
	ComputeEllipseTransform(e1,e2,NULL,IT);
	AffineTransformImage(im1,im2,NULL,IT);
	free(e1); free(e2); FreeDMatrix(IT,0,0);
	
}	
			
void RegionToPatch( Region key, Image source, Image patch, float scale ) {
	
	if ( key == NULL ) return;
	if ( !ImageIsGood(key->image) ) return;
	if ( !ImageIsGood(patch) ) return;
	
	double **IT = AllocDMatrix(3,3,0,0);
	double **TR = AllocDMatrix(3,3,0,0);
	int rad = patch->rows/2;
	Ellipse e1 = NewEllipse(key->row,key->col,key->maj*scale,key->min*scale,key->phi);
	Ellipse e2 = NewEllipse(rad,rad,rad,rad,key->phi);
	ComputeEllipseTransform(e1,e2,TR,IT); free(e1); free(e2);
	SeparableAffineTransform(source,patch,TR,IT);
	
}

Descriptor NewDescriptor( Region key, int dlength, char dtype, float *d ) {
	if ( key == NULL || d == NULL ) return NULL;
	Descriptor des = malloc(sizeof(struct DescriptorSt));
	if ( des == NULL ) return NULL;
	des->descriptortype = dtype;
	des->descriptorlength = dlength;
	des->row = key->row;
	des->col = key->col;
	des->ori = key->phi;
	des->descriptor = d;
	return des;
}

float *GLOHDescriptorFromPatch( Image patch, int pb, int ob ) {
	
	int maxRow = patch->rows-1;
	int maxCol = patch->cols-1;
	
	float radIncrement = (float)maxRow / pb;
	int patchCenter = maxRow / 2;
	
	float orientationIncrement = 360.0 / ob;
	
	int descriptorSize = pb * ob;
	float *descriptor = malloc(sizeof(float)*descriptorSize);
	
	int r,c;
	
	for (r=0;r<descriptorSize;r++) descriptor[r] = 0.0;
	
	for (r=1;r<maxRow;r++) {
		for (c=1;c<maxCol;c++) {
			float mRad = sqrt( ( r - patchCenter ) * ( r - patchCenter ) + ( c - patchCenter ) * ( c - patchCenter ) );
			int radiusBin = mRad / radIncrement;
			if ( radiusBin >= pb ) continue;
			int pixA = patch->pixels[r-1][c];
			int pixB = patch->pixels[r+1][c];
			int pixC = patch->pixels[r][c+1];
			int pixD = patch->pixels[r][c-1];
			if ( pixA < 0 || pixB < 0 || pixC < 0 || pixD < 0 ) continue;
			int mag = sqrt( (pixA-pixB)*(pixA-pixB) + (pixC-pixD)*(pixC-pixD) );
			float orientation = atan2(pixA-pixB,pixC-pixD)*DEG;
			if ( orientation < 0 ) orientation += 360;
			int orientationBin = ( orientation / orientationIncrement ) + 0.5;
			if ( orientationBin >= ob ) continue;
			descriptor[radiusBin*ob+orientationBin] += mag;
	}}
	
	return descriptor;
	
}	
	
float *PCADescriptorFromPatch( Image patch ) {
	#define PatchSize  41
	#define PatchLength (PatchSize * PatchSize)
	#define GPLEN ((PatchSize - 2) * (PatchSize - 2) * 2)
	#define PCALEN 36
	#define EPCALEN 36 
	#define PatchMag 20

	float *kv = malloc(sizeof(float)*PatchLength*2);
	
	/*
	int i, j;
	static float *avgs= NULL, **eigs;
	if ( avgs == NULL ) {
		float val;
		fprintf(stderr, "Attepting to open any pcavects.txt file!\n");
		FILE *pcaf = fopen("pcavects.txt", "rb");
		if ( pcaf == NULL ) { fprintf(stderr,"No valid pcavects.txt file!\n"); return NULL; }
		avgs = malloc(sizeof(float)*GPLEN);
		eigs = AllocFMatrix(EPCALEN,GPLEN,0,0);
		for (i=0;i<GPLEN;++i) {
			if (fscanf(pcaf, "%f", &val) != 1) {fprintf(stderr,"No valid pcavects.txt file!\n");return NULL;}
			avgs[i] = (float)val;
		}
		for (i=0;i<GPLEN;++i) {
			for (j=0;j<PCALEN;j++) {
				if (fscanf(pcaf,"%f", &val) != 1) {fprintf(stderr,"No valid pcavects.txt file!\n");return NULL;}
				if (j<EPCALEN) eigs[j][i] = (float)val;
			}
		}
		fclose(pcaf);
	}
	*/
	
	int count=0, **p1 = patch->pixels, row, col;
	for (row=1;row<PatchSize-1;++row) {
		for (col=1;col<PatchSize-1;++col) {	
			int a = p1[row][col+1];
			int b = p1[row][col-1];
			int c = p1[row-1][col];
			int d = p1[row+1][col];
			if ( a<0 || b<0 || c<0 || d<0 ) {
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
		for (row=0;row<GPLEN;++row) kpdescriptor[count] += eigs[row][count]*kv[row];
		//for (row=0;row<GPLEN;++row) kpdescriptor[count] += eigs[count][row]*kv[row];
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

void DrawSizeFVec(FVec sizes, int im_rmin, int im_cmin, int im_rmax, int im_cmax, int v, int stable, Image out );

void DrawRegion( Region key, float scale ) {
	
	if ( key == NULL ) return;
	
	int stable = key->stable;
	
	char name[256];
	sprintf(name,"/tmp/T%03d.ppm",stable);
	Image out = ReadPPMFile(name);
	
	static int count = 0;
	
	if ( !ImageIsGood(out) ) {
		out = ConvertImage1(CopyImage(key->image));
		sprintf(name,"/tmp/R%05d.ppm",count++);
	} else sprintf(name,"/tmp/T%03d.ppm",stable);
	
	fprintf(stderr,".");
	
	int rv = RandomNumber(0,255);
	int gv = RandomNumber(0,rv);
	int bv = RandomNumber(0,gv);
	
	int color = PIX3(rv,gv,bv);
	
	DrawPolygon(key->border,out,color);
	
	Ellipse e1 = NewEllipse(key->row,key->col,key->maj*scale,key->min*scale,key->phi);
	DrawEllipse(e1,out,color); free(e1);
	Image patch = CreateImage(41*sqrt(2),41*sqrt(2));
	RegionToPatch(key,key->image,patch,scale);

	FVec hist = GenerateOrientationHistogram(patch);
	GaussianBlur1D(hist->values,hist->l,hist->r,2);
	DrawFVec(hist,10,10,200,400,PIX3(0,0,250),out);
	FVecFree(hist);
	
	if ( PolygonIsGood(key->sizes) ) {
		
		struct PointSt p1 = key->sizes->vertices[0];
		struct PointSt p2 = key->sizes->vertices[key->sizes->numberOfVertices-1];

		int i;
		hist = FVecNew(0,255);
		Point p;
		while ( ( p = NextPolygonVertex(key->sizes) ) != NULL ) FVecSetAt(hist,p->y,p->x);
		if ( p1.y < p2.y ) {
			for(i=p1.y;i<=p2.y;i++) if ( hist->values[i] == 0.0 ) FVecAddAt(hist,i,1);
		} else {
			for(i=p2.y;i>=p1.y;i--) if ( hist->values[i] == 0.0 ) FVecAddAt(hist,i,1);
		}
		
		hist->l = MIN(p1.y,p2.y);
		hist->r = MAX(p2.y-1,p1.y-1);
		
		DrawSizeFVec(hist,497,0,1021,1023,color,stable,out);
		DrawSizeFVec(hist,498,0,1022,1023,color,stable,out);
		DrawSizeFVec(hist,499,0,1023,1023,color,stable,out);
		
	}
	
	WritePPM(name,out);
	FreeImage(out);

}

void DrawSizeFVec(FVec sizes, int im_rmin, int im_cmin, int im_rmax, int im_cmax, int v, int stable, Image out ) {
	
	int maxcol = out->cols-1;
	int maxrow = out->rows-1;
	
	int k, l = sizes->l, r = sizes->r;
	float large = sizes->values[l], small = sizes->values[l];
	for (k=l;k<=r;k++) large = MAX(large,sizes->values[k]);
	for (k=l;k<=r;k++) small = MIN(small,sizes->values[k]);
	
	int vec_cmax = r;
	int vec_cmin = l;
	int vec_rmax = large;
	int vec_rmin = small;

	double **tr = AllocDMatrix(3,3,0,0);
	CreateDirectAffineTransform( vec_rmax,vec_cmax, vec_rmin,vec_cmin, vec_rmin,vec_cmax, im_rmin,im_cmax, im_rmax,im_cmin, im_rmax,im_cmax, tr,NULL);

	for (k=l;k<r;k++) {
	
		float r1 = sizes->values[k];
		float r2 = sizes->values[k+1];
		float c1 = k;
		float c2 = k+1;
		
		float r1n = r1*tr[0][0]+c1*tr[1][0]+tr[2][0];
		float c1n = r1*tr[0][1]+c1*tr[1][1]+tr[2][1];
		float r2n = r2*tr[0][0]+c2*tr[1][0]+tr[2][0];
		float c2n = r2*tr[0][1]+c2*tr[1][1]+tr[2][1];
		
		r1n = MAX(0,MIN(r1n,maxrow));
		c1n = MAX(0,MIN(c1n,maxcol));
		r2n = MAX(0,MIN(r2n,maxrow));
		c2n = MAX(0,MIN(c2n,maxcol));
		
		int v1 = v;
		float sizeChange = (MAX(r1,r2)-MIN(r1,r2))/MIN(r1,r2);
		if ( sizeChange > 0.03 ) v1 = PIX3(255,0,0);
		else v1 = PIX3(0,255,0);
		if ( c1 == stable ) v1 = PIX3(0,0,255);
		
		FastLineDraw(r1n,c1n,r2n,c2n,out,v);
		
		SetImagePixel1(out,r1n,c1n,v1);
		SetImagePixel1(out,r1n+1,c1n,v1);
		SetImagePixel1(out,r1n-1,c1n,v1);
		SetImagePixel1(out,r1n,c1n+1,v1);
		SetImagePixel1(out,r1n,c1n-1,v1);
		
		
		
	}

	FreeDMatrix(tr,0,0);
	
}
