#include "mser.h"
#include "unionfind.h"
#include "ellipsefit.h"

void DrawSizeFVec(FVec sizes, float ms, int stable, Image out );
void DrawFVec(FVec sizes, int im_rmin, int im_cmin, int im_rmax, int im_cmax, int v, Image out );

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

