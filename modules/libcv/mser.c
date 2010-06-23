#include "util.h"
#include "mser.h"
#include "unionfind.h"
#include "geometry.h"

Ellipse FilterEllipse( Ellipse e );
void DrawRegion( Region key, float scale );
void ResetMSERArray( MSERArray pa );
MSERArray FreeMSERArray( MSERArray pa );
MSERArray ImageToMSERArray( Image image );
char MSERArrayIsGood( MSERArray array );
void EvaluateStableRegions( MSERArray ma, void **tSizes, PStack regions);
void FindBorder( Image image, int row, int col, int t, Polygon borderPixels );
void JoinNeighborsBelow( MSERArray ma, void **, int minSize, int maxSize );
void JoinNeighborsAbove( MSERArray ma, void **, int minSize, int maxSize );
void DrawConnectedRegions( MSERArray ma, int t, int minSize, int maxSize );


char libCV_above = FALSE;
char libCV_below = FALSE;

char FindMSERegions( Image image, PStack regions, float minSize, float maxSize, float blur, float sharpen, char u, char d ) {
	
	if ( !ImageIsGood(image) || !PStackGood(regions) ) return FALSE;
	
	int i, min = 0, max = 0;
	for (i=0;i<image->rows*image->cols;i++) {
		int pix = image->pixels[0][i];
		if ( pix < min ) min = pix;
		if ( pix > max ) max = pix;
	}
	
	fprintf(stderr,"Image min and max are %d %d\n",min,max);
	image->minv = min;
	image->maxv = max;
	EnhanceImage(image,0,1024,0.01,0.01);

	MSERArray ma = ImageToMSERArray(image);
	if ( minSize <= 1.0 ) minSize = minSize*ma->size;
	if ( maxSize <= 1.0 ) maxSize = maxSize*ma->size;

	void **sizes = malloc(sizeof(void **)*ma->size);
	int k; for (k=0;k<ma->size;k++) sizes[k] = NULL;
	
	if ( d ) {
		libCV_below = TRUE;
		libCV_above = FALSE;
		JoinNeighborsBelow(ma,sizes,minSize,maxSize);
		EvaluateStableRegions(ma,sizes,regions);
	}
	
	if ( u ) {
		libCV_below = FALSE;
		libCV_above = TRUE;
		JoinNeighborsAbove(ma,sizes,minSize,maxSize);
		EvaluateStableRegions(ma,sizes,regions);
	}
	
	FreeMSERArray( ma ); free(sizes);

	return TRUE;
	
}

void EvaluateStableRegions( MSERArray ma, void **tSizes, PStack regions) {
	
	int i; TSize tSize, oldTSize;
	Polygon polygon = NewPolygon(1000);
	float total;
	
	int *hist = malloc(sizeof(int)*101);

	total = 0;
	for (i=0;i<=100;i++) hist[i] = 0;
	for (i=0;i<ma->size;i++) {
		if ( tSizes[i] == NULL ) continue;	
		for ( tSize = tSizes[i]; tSize->next != NULL; tSize = tSize->next ) {
			float newSize = tSize->size;
			float oldSize = tSize->next->size;
			int sizeChange = ( ( newSize - oldSize ) / oldSize ) * 1000;
			tSize->size = sizeChange;
			if ( sizeChange == 0  ) continue;
			if ( sizeChange > 100 ) continue;
			hist[sizeChange]++;
			total++;
		}
	}

	int minStable, maxVal = total * 0.5; total = 0;
	for ( minStable = 0; total < maxVal && minStable <= 100; minStable++ ) total += hist[minStable];

	total = 0;
	for (i=0;i<=100;i++) hist[i] = 0;
	for (i=0;i<ma->size;i++) {
		if ( tSizes[i] == NULL ) continue;	
		tSize = tSizes[i];
		int lastSpike  = tSize->time;
		int mostStable = minStable;
		int bestStable = lastSpike;
		for ( tSize=tSizes[i];tSize->next!=NULL;tSize=tSize->next) {
			
			int sizeChange = tSize->size;
			tSize->size = 0;
			
			if ( sizeChange < mostStable ) {
				mostStable = sizeChange;
				bestStable = tSize->time;
			}
			
			if ( sizeChange > minStable ) {
				int period = ABS( tSize->time - lastSpike );
				tSize->time = ( tSize->time + lastSpike ) / 2;
				tSize->size = period;
				lastSpike = tSize->time;
				bestStable = lastSpike;
				mostStable = minStable;
				if ( period > 20 ) continue;
				hist[period]++;
				total++;
			}
			
		}
	}
	
	int minPeriod; maxVal = total * 0.95; total = 0;
	for ( minPeriod = 0; total < maxVal && minPeriod <= 100; minPeriod++ ) total += hist[minPeriod];
	
	for (i=0;i<ma->size;i++) {
		if ( tSizes[i] == NULL ) continue;	
		for ( tSize=tSizes[i];tSize->next!=NULL;tSize=tSize->next) {
			int period = tSize->size;
			if ( period > minPeriod ) {
				int treshold = tSize->time;
				int row = i / ma->cols;
				int col = i % ma->cols;
				FindBorder(ma->image,row,col,treshold,polygon);
				Ellipse e = CalculateEllipseFromPolygon( polygon );
				Region newRegion = NewRegion(e,ma->image,NULL,polygon,treshold,i);
				PushPStack(regions,newRegion);
				if ( e != NULL ) free(e);
			}
		}
	}

	for (i=0;i<ma->size;i++) {
		if ( tSizes[i] == NULL ) continue;	
		tSize = tSizes[i];
		while ( tSize != NULL ) {
			oldTSize = tSize;
			tSize = tSize->next;
			free(oldTSize);
		}
		tSizes[i] = NULL;
	}
	
	//fprintf(stderr,"Mean stability : %d  ", minStable);
	//fprintf(stderr,"Mean period : %d\n", minPeriod);
	
	FreePolygon(polygon);
	free(hist);
	
}

void JoinNeighborsBelow( MSERArray ma, void **sizes, int minSize, int maxSize ) {
	
	ResetMSERArray(ma);
	
	int i, r, p, t;
	
	int *stack = malloc(sizeof(int)*ma->size);
	int stackSize = 0;
	int curSize = 0;

	int rd = 1;
	int cd = ma->cols;
	
	for (t=ma->minv;t<=ma->maxv;t++) {
		
		int tMin = ma->sb[t];
		int tMax = ma->sb[t+1];
		while ( tMin < tMax ) {
			p = ma->sp[tMin++];
			r = Find(ma->roots,p);
			if ( ma->tvals[p-rd] <= t ) r = UnionFindB(ma->roots,ma->sizes,r,p-rd);
			if ( ma->tvals[p+rd] <= t ) r = UnionFindB(ma->roots,ma->sizes,r,p+rd);
			if ( ma->tvals[p-cd] <= t ) r = UnionFindB(ma->roots,ma->sizes,r,p-cd);
			if ( ma->tvals[p+cd] <= t ) r = UnionFindB(ma->roots,ma->sizes,r,p+cd);
			if ( ma->sizes[r] < minSize ) continue;
			if ( ma->flags[r] == 1 ) continue;
			stack[stackSize++] = r;
			ma->flags[r] = 1;
		}
		
		curSize = 0;
		for (i=0;i<stackSize;i++) {
			r = stack[i];
			if ( ma->roots[r] != r ) continue;
			if ( ma->sizes[r] > maxSize ) continue;
			TSize tSize = malloc(sizeof(struct TSizeSt));
			tSize->next = sizes[r];
			sizes[r] = tSize;
			tSize->size = ma->sizes[r];
			tSize->time = t;
			stack[curSize++] = r;
		}
		stackSize = curSize;
		
	}
	
	free(stack);
	
}

void JoinNeighborsAbove( MSERArray ma, void **sizes, int minSize, int maxSize ) {
	
	ResetMSERArray(ma);
	
	int i, r, p, t;
	
	int *stack = malloc(sizeof(int)*ma->size);
	int stackSize = 0;
	int curSize = 0;

	int rd = 1;
	int cd = ma->cols;
	
	for (t=ma->maxv;t>=ma->minv;t--) {
		
		int tMin = ma->sb[t];
		int tMax = ma->sb[t+1];
		while ( tMin < tMax ) {
			p = ma->sp[tMin++];
			r = Find(ma->roots,p);
			if ( ma->tvals[p-rd] >= t ) r = UnionFindB(ma->roots,ma->sizes,r,p-rd);
			if ( ma->tvals[p+rd] >= t ) r = UnionFindB(ma->roots,ma->sizes,r,p+rd);
			if ( ma->tvals[p-cd] >= t ) r = UnionFindB(ma->roots,ma->sizes,r,p-cd);
			if ( ma->tvals[p+cd] >= t ) r = UnionFindB(ma->roots,ma->sizes,r,p+cd);			
			if ( ma->sizes[r] < minSize ) continue;
			if ( ma->flags[r] == 1 ) continue;
			stack[stackSize++] = r;
			ma->flags[r] = 1;
		}
		
		curSize = 0;
		for (i=0;i<stackSize;i++) {
			r = stack[i];
			if ( ma->roots[r] != r ) continue;
			if ( ma->sizes[r] > maxSize ) continue;
			TSize tSize = malloc(sizeof(struct TSizeSt));
			tSize->next = sizes[r];
			sizes[r] = tSize;
			tSize->size = ma->sizes[r];
			tSize->time = t;
			stack[curSize++] = r;
		}
		stackSize = curSize;
		
	}
	
	free(stack);

}

char TestRC( Image im, int r, int c, int t ) {
	if ( r < 1 ) return FALSE;
	if ( c < 1 ) return FALSE;
	if ( r >= im->rows-1 ) return FALSE;
	if ( c >= im->cols-1 ) return FALSE;
	if ( im->pixels[r][c] == t ) return TRUE;
	if ( im->pixels[r][c] < t ) return libCV_below;
	else return libCV_above;
}

void FindBorder( Image image, int row, int col, int t, Polygon borderPixels ) {
	
	if ( !ImageIsGood(image) || !PolygonIsGood(borderPixels) ) {
		Debug(1,"FastFindBorder: Input image or polygon is broken.\n");
		return;
	}
	
	if ( libCV_above == TRUE ) Debug(1,"FastFindBorder: Including pixels >= %d.\n",t);
	if ( libCV_below == TRUE ) Debug(1,"FastFindBorder: Including pixels <= %d.\n",t);
	
	int dr[4], dc[4], lt[4], rt[4];
	dr[0] = 0; dr[1] = -1; dr[2] =  0; dr[3] = 1;
	dc[0] = 1; dc[1] =  0; dc[2] = -1; dc[3] = 0;
	lt[0] = 1, lt[1] =  2, lt[2] =  3; lt[3] = 0;
	rt[0] = 3, rt[1] =  0; rt[2] =  1; rt[3] = 2;
	
	int srow = row;
	int scol = image->cols;
	int i, d = 2, ld = 1, sd = 1;
	
	do {
		
		if ( col < scol && row == srow ) {
			while ( TestRC(image,row,col-1,t) ) col--;
			if ( col != scol ) {
				scol = col; borderPixels->numberOfVertices = 0; ld = 0; sd = 3;
				if ( TestRC(image,row,col+1,t) ) sd = 2;
				if ( TestRC(image,row+1,col,t) ) sd = 1;
			}
		}
		
		if ( row > 1 && col > 1 && row < image->rows-2 && col < image->cols-2 )
			AddPolygonVertex(borderPixels,row,col);
		
		for (d=lt[ld],i=0;i<4;i++,d=rt[d])
			if ( TestRC(image,row+dr[d],col+dc[d],t) ) break;
		
		if ( i == 4 ) break;
		
		row += dr[d];
		col += dc[d];
		
		ld = d;
		
	} while ( row != srow || col != scol || d != sd );
}

void ResetMSERArray( MSERArray ma ) {
	if ( !MSERArrayIsGood(ma) ) return;
	int k, max = ma->size;
	for (k=0;k<max;++k) ma->sizes[k] = 1;
	for (k=0;k<max;++k) ma->roots[k] = k;
	for (k=0;k<max;++k) ma->flags[k] = 0;
}

MSERArray FreeMSERArray( MSERArray pa ) {
	if ( pa == NULL ) return NULL;
	if ( pa->sb+pa->minv != NULL )	free(pa->sb+pa->minv);
	if ( pa->sp != NULL )				free(pa->sp);
	if ( pa->roots != NULL )			free(pa->roots);
	if ( pa->sizes != NULL )			free(pa->sizes);
	if ( pa->flags != NULL )			free(pa->flags);
	free(pa);
	return NULL;
}

char MSERArrayIsGood( MSERArray array ) {
	if ( array == NULL ) return FALSE;
	if ( array->sizes == NULL ) return FALSE;
	if ( array->flags == NULL ) return FALSE;
	if ( array->roots == NULL ) return FALSE;
	if ( array->sp == NULL ) return FALSE;
	if ( array->sb + array->minv == NULL ) return FALSE;
	return TRUE;
}

MSERArray ImageToMSERArray( Image image ) {
	
	if ( !ImageIsGood(image) ) return NULL;
	if ( !ImageRangeDefined(image) ) FindImageLimits(image);

	int maxrow   	= image->rows;
	int maxcol   	= image->cols;
	int maxv 		= image->maxv;
	int minv 		= image->minv;
	int arraymax 	= maxcol*maxrow;
	int maxr 		= maxrow - 2;
	int maxc 		= maxcol - 2;
	
	MSERArray mser = malloc(sizeof(struct MSERArraySt));
	if ( mser == NULL ) return NULL;
	
	mser->rows  = maxrow;
	mser->cols  = maxcol;
	mser->maxv  = maxv;
	mser->minv  = minv;
	mser->size  = arraymax;
	mser->image = image;

	mser->tvals 	= image->pixels[0];	
	mser->roots 	= malloc(arraymax*sizeof(int));
	mser->sizes 	= malloc(arraymax*sizeof(int));
	mser->flags 	= malloc(arraymax*sizeof(int));
	mser->sp		= malloc(sizeof(int)*maxr*maxc);
	mser->sb		= ((int *)malloc(sizeof(int)*(maxv-minv+2))) - minv;
	
	if ( !MSERArrayIsGood(mser) ) return FreeMSERArray(mser);
 
	int k,r,c;
	int **p = image->pixels;
	int *sp = mser->sp;
	int *sb = mser->sb;
	for (k=minv;k<=maxv+1;k++) sb[k] = 0;
	for (r=1;r<=maxr;r++) for (c=1;c<=maxc;c++) sb[p[r][c]]++;
	for (k=minv;k<=maxv;k++) sb[k+1] += sb[k];
	for (r=1;r<=maxr;r++) for (c=1;c<=maxc;c++) sp[--sb[p[r][c]]] = r*(maxcol)+c;

	return mser;
	
}

Region NewRegion( Ellipse e, Image image, Polygon sizes, Polygon border, int stable, int root ) {

	if ( e == NULL ) return NULL;
	
	Region reg = malloc(sizeof(struct RegionSt));
	if ( reg == NULL ) return NULL;
	
	reg->root   = root;
	reg->stable = stable;
	reg->border = CopyPolygon(border);
	reg->sizes  = CopyPolygon(sizes);
	
	reg->image = image;
	reg->row = e->x;
	reg->col = e->y;
	reg->maj = e->majorAxis;
	reg->min = e->minorAxis;
	reg->phi = e->phi;
	reg->ori = e->phi*DEG;
	reg->A = e->A;
	reg->B = e->B;
	reg->C = e->C;
	reg->D = e->D;
	reg->E = e->E;
	reg->F = e->F;
	reg->minr = e->topBound;
	reg->maxr = e->bottomBound;
	reg->minc = e->leftBound;
	reg->maxc = e->rightBound;
	
	return reg;
	
}

void freeRegion( Region reg ) {
	
	FreePolygon(reg->sizes);
	FreePolygon(reg->border);
	free(reg);
	
}
	
void DrawConnectedRegions( MSERArray ma, int t, int minSize, int maxSize ) {
	
	char name[256];
	
	static int *colors = NULL;
	static int size = 0;
	
	int rr = 100;
	int er = 200;
	
	int k;
	
	if ( size != ma->size ) {
		size = ma->size;
		colors = malloc(sizeof(int)*size);
		for (k=0;k<size;k++) colors[k] = 0;
	}
	
	sprintf(name,"/tmp/V%03d.ppm",t);
	fprintf(stderr,"Wrote %s to disk.\n",name);
	Image out = ConvertImage1(CopyImage(ma->image));
	
	int *pixels = out->pixels[0];
	
	int *stack = malloc(sizeof(int)*size);
	int *flags = malloc(sizeof(int)*size);
	int stackSize = 0;
	
	for (k=0;k<size;k++) flags[k] = 0;
	
	for (k=0;k<size;k++) {
		int r = Find(ma->roots,k);
		if ( ma->sizes[r] <= 1 ) continue;
		if ( colors[r] == 0 ) {
			int rv = RandomNumber(rr,er);
			int gv = RandomNumber(rr,er);
			int bv = RandomNumber(rr,er);
			colors[r] = PIX3(rv,gv,bv);
		}
		pixels[k] = colors[r];
		if ( flags[r] == 1 ) continue;
		if ( ma->sizes[r] < minSize ) continue;
		if ( ma->sizes[r] > maxSize ) continue;
		stack[stackSize++] = r;
		flags[r] = 1;
	}
	
	Polygon bp = NewPolygon(1000);
	
	for(k=0;k<stackSize;k++) {
		int r = stack[k];
		if ( ma->roots[r] != r ) continue;
		int row = r / ma->cols;
		int col = r % ma->cols;
		FindBorder(ma->image,row,col,t,bp);
		DrawPolygon(bp,out,colors[r]>>1);
	}
	
	free(flags); free(stack);
	
	FreePolygon(bp);
	WritePPM(name,out);
	FreeImage(out);

}
