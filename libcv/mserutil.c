#include "defs.h"
#include "mser.h"
#include "unionfind.h"
#include "ellipsefit.h"

void DrawSizeFVec(FVec sizes, float ms, int stable, Image out );
void DrawFVec(FVec sizes, int im_rmin, int im_cmin, int im_rmax, int im_cmax, int v, Image out );

void DrawConnectedRegions( MSERArray ma ) {
	
	char name[256];
	
	static int *colors = NULL;
	static int    size = 0;
	
	int k, maxcol = ma->cols;
	
	int RE = PIX3(255,0,0);
	int BL = PIX3(0,0,255);
	int GR = PIX3(0,255,0);
	
	if ( size != ma->size ) {
		size = ma->size;
		if ( colors != NULL ) free(colors);
		colors = malloc(sizeof(int)*size);
		for (k=0;k<size;k++) colors[k] = 0;
	}
	static int count = 0;
	sprintf(name,"/tmp/T%03d.ppm",count++);
	fprintf(stderr,"Writing %s to disk.\n",name);
	
	Image out = ConvertImage1(CopyImage(ma->image));
	
	int *roots = ma->roots;
	int *sizes = ma->sizes;
	char *flags = ma->flags;
	int *pixels = out->pixels[0];
	
	int *in = malloc(sizeof(int)*size);
	int *sa = malloc(sizeof(int)*size);
	int si = 0;
	int fa = rand();
	
	for (k=0;k<size;k++) {
		int r = Find(roots,k);
		if ( sizes[r] <= 1 ) continue;
		if ( colors[r] == 0 ) {
			int rv = ((float)rand()/RAND_MAX)*50+200;
			int gv = ((float)rand()/RAND_MAX)*50+200;
			int bv = ((float)rand()/RAND_MAX)*50+200;
			colors[r] = PIX3(rv,gv,bv);
		}
		pixels[k] = colors[r];
		if ( in[r] != fa ) { sa[si++] = r; in[r] = fa; }
	}
	
	while ( si > 0 ) {
		int r = sa[--si];
		int row = r/maxcol;
		int col = r%maxcol;
		if ( flags[r] == 1 ) {
			SetImagePixel1(out,row,col,RE);
			FastLineDraw(row-3,col-3,row+3,col-3,out,BL);
			FastLineDraw(row+3,col-3,row+3,col+3,out,BL);
			FastLineDraw(row+3,col+3,row-3,col+3,out,BL);
			FastLineDraw(row-3,col+3,row-3,col-3,out,BL);
		}
		if ( flags[r] == 0 ) {
			//SetImagePixel1(out,row,col,RE);
			//FastLineDraw(row-1,col-1,row+1,col-1,out,RE);
			//FastLineDraw(row+1,col-1,row+1,col+1,out,RE);
			//FastLineDraw(row+1,col+1,row-1,col+1,out,RE);
			//FastLineDraw(row-1,col+1,row-1,col-1,out,RE);
		}
		if ( flags[r] == 2 ) {
			SetImagePixel1(out,row,col,RE);
			FastLineDraw(row-4,col-4,row+4,col-4,out,GR);
			FastLineDraw(row+4,col-4,row+4,col+4,out,GR);
			FastLineDraw(row+4,col+4,row-4,col+4,out,GR);
			FastLineDraw(row-4,col+4,row-4,col-4,out,GR);
		}
	}
	
	WritePPM(name,out);
	FreeImage(out);
	free(in);free(sa);
}

void DrawOrientations( float *bins, Image out, float ori ) {
	int k;
	float largest = 0;
	for (k=0;k<360;k++) largest = MAX(largest,bins[k]);
	largest = 1.0/largest;
	for (k=0;k<359;k++) {
		int p1row = 110-bins[k]*100*largest;
		int p1col = k+220;
		int p2row = 110-bins[k+1]*100*largest;
		int p2col = k+221;
		if ( p1row < 0 || p1row >= out->rows || p1col < 0 || p1col >= out->cols ) continue;
		if ( p2row < 0 || p2row >= out->rows || p2col < 0 || p2col >= out->cols ) continue;
		FastLineDraw(p1row,p1col,p2row,p2col,out,PIX3(255,255,0));
	}
	if ( ori < 0 ) ori += 360;
	FastLineDraw(110,ori+220,10,ori+220,out,PIX3(255,0,0));
	FastLineDraw(110-0.9*100,220,110-0.9*100,359+221,out,PIX3(255,0,0));
}

void DrawRegion( Region key ) {
	
	if ( key == NULL ) return;
	
	static int count = 1;
	char name[256];
	Image out = ConvertImage1(CopyImage(key->image));
	sprintf(name,"/tmp/T%05d.ppm",count++);
	fprintf(stderr,"Writing image %s to disk.\n", name);
	int wlen = 101;
	int maxcol = out->cols;
	
	int RE = PIX3(255,0,0);
	int BL = PIX3(0,0,255);
	int GR = PIX3(0,255,0);
	
	
	static Image patch, mags = NULL;
	if ( mags == NULL ) {
		mags  = CreateImage(wlen,wlen);
		patch = CreateImage(wlen,wlen);
	}
	
	
	DrawEllipse(NewEllipse(key->row,key->col,key->maj,key->min,key->phi),out,PIX3(0,255,0));
	
	
	ClearImage(patch,0);
	ClearImage(mags,0);
	int **p1 = patch->pixels;

	RegionToPatch(key,patch);
	/*
	float *desc = CreateSIFTDescriptor(patch,4,8);
	struct FVecSt de;
	de.values = desc;
	de.l=0;
	de.r=4*4*8-1;
	de.max_r=de.r;
	de.max_l=de.l;
	
	DrawFVec(&de,10,600,110,1000,PIX3(0,255,0),out);
	free(desc);
	
	if ( maxcol <= wlen*2 ) return;

	int wroff = 10;
	int wcoff = 10;
	
	int row, col;

	for (row=0;row<wlen;row++) {
		for (col=0;col<wlen;col++) {
			int val = p1[row][col];
			val = MAX(0,MIN(val,255));
			SetImagePixel3(out,row+wroff,col+wcoff,val,val,val);
			float mag = 0;
			if (row-1<0||col-1<0||row+1>=wlen||col+1>=wlen) continue;
			int a = p1[row][col+1];
			int b = p1[row][col-1];
			int c = p1[row-1][col];
			int d = p1[row+1][col];
			if ( a<0||b<0||c<0||d<0 ) mags->pixels[row][col] = 0;
			else {
				float vmag = c-d;
				float hmag = a-b;   
				mag = sqrt(hmag*hmag+vmag*vmag);
				mag = MAX(0,MIN(mag,255));
				mags->pixels[row][col] = mag;
			}
		}
	}

	EnhanceImage(mags,0,255,0.01,0.01);
	
	for (row=0;row<wlen;row++) {
		for (col=0;col<wlen;col++) {
			if (row-1<0||col-1<0||row+1>=wlen||col+1>=wlen) continue;
			int p = mags->pixels[row][col];
			SetImagePixel3(out,row+wroff,col+wcoff+wlen,p,p,p);
		}
	}
	
	FastLineDraw(wlen+wroff,wcoff,wlen+wroff,wlen*2+wcoff,out,PIX3(0,0,255));
	FastLineDraw(wroff,wcoff,wroff,wlen*2+wcoff,out,PIX3(0,0,255));
	FastLineDraw(wroff,wcoff,wlen+wroff,wcoff,out,PIX3(0,0,255));
	FastLineDraw(wroff,wlen*2+wcoff,wlen+wroff,wlen*2+wcoff,out,PIX3(0,0,255));
	
	int krow = key->root / maxcol;
	int kcol = key->root % maxcol;
	
	SetImagePixel1(out,krow,kcol,RE);
	FastLineDraw(krow-3,kcol-3,krow+3,kcol-3,out,BL);
	FastLineDraw(krow+3,kcol-3,krow+3,kcol+3,out,BL);
	FastLineDraw(krow+3,kcol+3,krow-3,kcol+3,out,BL);
	FastLineDraw(krow-3,kcol+3,krow-3,kcol-3,out,BL);
	*/
	if ( key->sizes != NULL ) {
		PointStack stack = key->sizes;
		int t1 = stack->items[0].row;
		int t2 = stack->items[stack->stacksize-1].row;
		FVec si = NewFVec(MIN(t1,t2),MAX(t1,t2));
		while ( PointStackCycle(stack) == TRUE ) {
			Point p = CyclePointStack(stack);
			SetFVec(si,(int)p->row,(float)p->col);
		}
		
		int k;
		if ( t1 < t2 ) {
			for(k=MIN(t1,t2)+1;k<=MAX(t1,t2);k++) if ( si->values[k] == 0 ) si->values[k] = si->values[k-1];
		} else {
			for(k=MAX(t1,t2)-1;k>=MIN(t1,t2);k--) if ( si->values[k] == 0 ) si->values[k] = si->values[k+1];
		}
		DrawSizeFVec(si,0.05,key->stable,out);
		FreeFVec(si);
	}
	
	if ( key->border != NULL ) DrawPointStack(key->border,out,PIX3(255,0,0));
	/*
	float *bins = malloc(sizeof(float)*360);
	for(wlen=0;wlen<360;wlen++) bins[wlen] = 0;
	GenerateGradientOrientationBins(key,key->image,bins);
	DrawOrientations(bins,out,key->ori);
	WrapGaussianBlur1D(bins,0,359,15);
	DrawOrientations(bins,out,key->ori);
	free(bins);
	*/
	WritePPM(name,out);
	FreeImage(out);

}

void DrawSizeFVec(FVec sizes, float ms, int stable, Image out ) {
	
	int maxcol = out->cols-1;
	int maxrow = out->rows-1;
	
	int im_rmin = maxrow/2;
	int im_cmin = 0;
	int im_rmax = maxrow-100;
	int im_cmax = maxcol;
	
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
		
		FastLineDraw(r1n,c1n,r2n,c2n,out,PIX3(0,255,0));
		
		if ( ABS(r1-r2) > ms*MIN(r1,r2) ) {
			FastLineDraw(maxrow,c1n,r1n-10,c1n,out,PIX3(255,0,0));
			FastLineDraw(maxrow,c2n,r2n-10,c2n,out,PIX3(255,0,0));
		}
		
		if ( k+1 == stable ) FastLineDraw(r1n-10,c2n,r1n+10,c2n,out,PIX3(0,0,255));
		
	}
	
	FreeDMatrix(tr,0,0);
	
}

void DrawRegionOnConnectedRegions( Region reg ) {
	
	int treshold = reg->stable;
	
	char name[256];
	sprintf(name,"/tmp/T%03d.ppm",255-treshold);
	
	Image out = ReadPPMFile(name);
	
	DrawPointStack(reg->border,out,PIX3(255,0,0));
	
	WritePPM(name,out);
	FreeImage(out);
	
}

