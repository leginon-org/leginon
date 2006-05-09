#include "defs.h"
#include "mser.h"
#include "unionfind.h"


char FindMSERegions( Image image, PStack regions, float minsize, float maxsize, float minperiod, float minstable ) {
	
	if ( !ImageGood(image) || !PStackGood(regions) ) return FALSE;
	
	MSERArray pa = ImageToMSERArray(image);
	
	int maxarea  = pa->size;
	int maxrange = pa->maxv - pa->minv;
	
	if ( minsize <= 1.0 ) minsize = MAX(maxarea*minsize,5);
	if ( maxsize <= 1.0 ) maxsize = maxarea*maxsize,maxarea;
	if ( minperiod <= 1.0 ) minperiod = MAX(minperiod*maxrange,1);
	
	fprintf(stderr,"Finding stable regions in image with %d pixels and dynamic range %d.\n",maxarea,maxrange);
	fprintf(stderr,"MinSize: %d pixels\nMaxSize: %d pixels\nMinPeriod: %d tresholds\nMinStable: %2.2f%% size growth\n",(int)minsize,(int)maxsize,(int)minperiod,minstable*100);
	
	TrackRegions(pa,regions,minsize,maxarea,minperiod,minstable);

	FreeMSERArray( pa ); 
	
	return TRUE;
	
}

void TrackRegions( MSERArray pa, PStack regions, int minsize, int maxsize, int minperiod, float minstable ) {

	int kmin, kmax, k;
	
	int *v1 = malloc(sizeof(int)*pa->size);
	int s1 = 0;
	
	ResetMSERArray(pa);
	for (k=pa->minv;k<=pa->maxv;k++) {	
		kmin = pa->sb[k];
		kmax = pa->sb[k+1];
		s1 = JoinNeighborsUp(pa->sp,pa->roots,pa->sizes,pa->tvals,pa->flags,pa->cols,k,kmin,kmax,v1,s1,minsize,maxsize);	
		s1 = ProcessTouchedRoots(pa->roots,pa->sizes,pa->flags,pa->regions,v1,s1,k);
	}
	DetermineStableRegions(pa,regions,1,minperiod,minstable);
	
	ResetMSERArray(pa);
	for (k=pa->maxv;k>=pa->minv;k--) {
		kmin = pa->sb[k];
		kmax = pa->sb[k+1];
		s1 = JoinNeighborsDown(pa->sp,pa->roots,pa->sizes,pa->tvals,pa->flags,pa->cols,k,kmin,kmax,v1,s1,minsize,maxsize);
		s1 = ProcessTouchedRoots(pa->roots,pa->sizes,pa->flags,pa->regions,v1,s1,k);
	}
	DetermineStableRegions(pa,regions,-1,minperiod,minstable);

	free(v1);
		
}

int JoinNeighbors( int *sp, int *roots, int *sizes, int *tvals, char *flags, int stride, int k, int kmin, int kmax, int *idle, int idlesize, int minsize, int maxsize ) {
	
	int r;
	
	while( kmin < kmax ) {
		r = Connect4(roots,sizes,stride,sp[kmin++]);
		switch ( flags[r] ) {
			case 3:
			case 2: break;
			case 1: flags[r] = 2;
					break;
			case 0: if ( sizes[r] < minsize ) break;
					if ( sizes[r] > maxsize ) break;
					flags[r] = 3;
					idle[idlesize++] = r;
					break;
		}
	}
	
	return idlesize;
}

int JoinNeighborsUp( int *sp, int *roots, int *sizes, int *tvals, char *flags, int stride, int k, int kmin, int kmax, int *idle, int idlesize, int minsize, int maxsize ) {
	
	int r;
	
	while( kmin < kmax ) {
		r = Connect4Up(roots,sizes,tvals,stride,sp[kmin++],k);
		switch ( flags[r] ) {
			case 3:
			case 2: break;
			case 1: flags[r] = 2;
					break;
			case 0: if ( sizes[r] < minsize ) break;
					if ( sizes[r] > maxsize ) break;
					flags[r] = 3;
					idle[idlesize++] = r;
					break;
		}
	}
	
	return idlesize;
}

int JoinNeighborsDown( int *sp, int *roots, int *sizes, int *tvals, char *flags, int stride, int k, int kmin, int kmax, int *idle, int idlesize, int minsize, int maxsize ) {
	
	int r;
	
	while( kmin < kmax ) {
		r = Connect4Down(roots,sizes,tvals,stride,sp[kmin++],k);
		switch ( flags[r] ) {
			case 3:
			case 2: break;
			case 1: flags[r] = 2;
					break;
			case 0: if ( sizes[r] < minsize ) break;
					if ( sizes[r] > maxsize ) break;
					flags[r] = 3;
					idle[idlesize++] = r;
					break;
		}
	}
	
	return idlesize;
}

int ProcessTouchedRoots( int *roots, int *sizes, char *flags, void **regions, int *idle, int idlesize, int tic ) {

	int temp[idlesize], tempsize = 0;
	
	while ( idlesize > 0 ) {
		int r = idle[--idlesize];
		switch ( flags[r] ) {
			case 3: if ( roots[r] != r ) break;
					regions[r] = NewPointStack(20);
			case 2: PushPointStack(regions[r],tic,sizes[r]);
					flags[r] = 1;
					temp[tempsize++] = r;
					break;
			case 1: if ( roots[r] != r ) PushPointStack(regions[r],tic,sizes[r]*2);
					else temp[tempsize++] = r;
					break;
		}
	}
	memcpy(idle,temp,sizeof(int)*tempsize);
	return tempsize;
	
}

void DetermineStableRegions( MSERArray pa, PStack regions, int ud, int minPeriod, float minStable ) {
	
	if ( !PStackGood(regions) ) return;
	
	FStack sp = NewFStack(10);
	PointStack bp = NewPointStack(10);
	
	char *flags = pa->flags;
	void **sizeStacks = pa->regions;
	int k;

	for (k=0;k<pa->size;k++) {

		if ( flags[k] == 0 ) continue;
		if ( flags[k] == 3 ) continue;
		PointStack sizes = sizeStacks[k];
		FindStablePeriods(sizes,sp,minPeriod,minStable);
		while ( !FStackEmpty(sp) ) {
			float s = PopFStack(sp);
			if (ud==1) CarveOutRegionUp(k,pa->image,bp,s);
			else CarveOutRegionDown(k,pa->image,bp,s);
			Ellipse e = CalculateAffineEllipse( bp, 3.0 );
			Region key = NewRegion(e,pa->image,sizes,bp,s,k);
			PushPStack(regions, key);
			if ( e != NULL ) free(e);
		}
		FreePointStack(sizes);
	}
	FreeFStack(sp);
	FreePointStack(bp);
}

void FindStablePeriods( PointStack sizes, FStack sp, int minPeriod, float minStable ) {
	
	if ( !PointStackGood(sizes) || !FStackGood(sp) ) return;
	if ( PointStackEmpty(sizes) ) return;
	
	Point p;
	float oldTime, oldSize, lastSpike, lastStable, period;
	float bestStability, curTime, curSize, currentChange;
	
	p = CyclePointStack(sizes);
	oldTime = p->row;
	oldSize = p->col;
	lastSpike = oldTime;
	lastStable = oldTime;
	bestStability = 1.0;
	
	while ( PointStackCycle(sizes) ) {
	
		p = CyclePointStack(sizes);
		
		curTime = p->row;
		curSize = p->col;
		
		currentChange = ( curSize - oldSize ) / oldSize;
		if ( currentChange > minStable ) {
			period = lastSpike - curTime;
			lastSpike = curTime;
			if ( ABS(period) > minPeriod ) { PushFStack(sp,lastStable);}
			lastStable = oldTime;
			bestStability = currentChange;
		} else if ( currentChange < bestStability ) {
			 bestStability = currentChange;
			 lastStable = curTime;
		}
		oldSize = curSize; oldTime = curTime;
	}

}

int SearchHoodUp1( int row, int col, int **p, int t1, float t, int maxrow, int maxcol ) {
	if ( t1<=t && row>=0 && row<maxrow && col>=0 && col<maxcol ) return 0;
	else if ( row>=0 && row<maxrow && col>=0 && col<maxcol && p[row][col]<=t ) return 0;		
	return 1;
}

int SearchHoodUp2( int row, int col, int **p, int t1, float t, int maxrow, int maxcol ) {
	if ( row < 0 || col < 0 || row >= maxrow || col >= maxcol ) return 1;
	if ( p[row][col] <= t ) return 0;
	return 1;
}

void CarveOutRegionUp( int root, Image image, PointStack borderpixels, float t ) {
	
	if ( image == NULL || borderpixels == NULL ) return;
	
	int maxrow = image->rows;
	int maxcol = image->cols;

	int **p = image->pixels;
	
	int row = root / maxcol;
	int col = root % maxcol;
	int leftmost = col;

	FStack leaving = NewFStack(3);

	int rightturns = 0;
	while ( rightturns <= 0 ) {
		
		int pt = p[row][col];
		
		rightturns=0; col=leftmost;
		while ( col > 0 && p[row][col-1] <= t ) col--;
		int srow = row;
		int scol = col;

		int direction = 0;
		int lastdirection = 0;
		int visits = 1;
		
		leaving->stacksize=0; borderpixels->stacksize=0;
		if ( SearchHoodUp2(row+1,col,p,pt,t,maxrow,maxcol)==0 ) PushFStack(leaving,3);
		if ( SearchHoodUp2(row,col+1,p,pt,t,maxrow,maxcol)==0 ) PushFStack(leaving,2);
		if ( SearchHoodUp2(row-1,col,p,pt,t,maxrow,maxcol)==0 ) PushFStack(leaving,1);

		do {
			
			if (row>0 && row<maxrow-1 && col>0 && col<maxcol-1) PushPointStack(borderpixels,row,col);
			
			int done=1;
			pt = p[row][col];
			while ( done ) {
				direction = (direction+1) % 4;
				if ( direction==0 ) if (SearchHoodUp2(row,col-1,p,pt,t,maxrow,maxcol)==0) {done=0;col--;}
				if ( direction==1 ) if (SearchHoodUp2(row-1,col,p,pt,t,maxrow,maxcol)==0) {done=0;row--;}
				if ( direction==2 ) if (SearchHoodUp2(row,col+1,p,pt,t,maxrow,maxcol)==0) {done=0;col++;}
				if ( direction==3 ) if (SearchHoodUp2(row+1,col,p,pt,t,maxrow,maxcol)==0) {done=0;row++;}
			}

			if ( direction != lastdirection ) {
				if ( direction == (lastdirection+3)%4 ) { rightturns--; }
				else if ( direction == (lastdirection+1)%4 ) { rightturns++; }
					else { rightturns += 2; }
			}

			if ( row == srow && col == scol && (direction+2)%4 != PopFStack(leaving) ) visits = 0;
			if ( row == srow && col < leftmost ) leftmost = col;
			lastdirection = direction;
			direction = (direction+2) % 4;
				
		} while ( visits );
	}
	FreeFStack(leaving);

}

int SearchHoodDown1( int row, int col, int **p, int t1, float t, int maxrow, int maxcol ) {
	if ( t1>=t && row>=0 && row<maxrow && col>=0 && col<maxcol ) return 0;
	else if ( row>=0 && row<maxrow && col>=0 && col<maxcol && p[row][col]>=t ) return 0;		
	return 1;
}

int SearchHoodDown2( int row, int col, int **p, int t1, float t, int maxrow, int maxcol ) {
	if ( row < 0 || col < 0 || row >= maxrow || col >= maxcol ) return 1;
	if ( p[row][col] >= t ) return 0;
	else return 1;
}

void CarveOutRegionDown( int root, Image image, PointStack borderpixels, float t ) {
	
	if ( image == NULL || borderpixels == NULL ) return;
	
	int maxrow = image->rows;
	int maxcol = image->cols;

	int **p = image->pixels;
	
	int row = root / maxcol;
	int col = root % maxcol;
	int leftmost = col;
	
	FStack leaving = NewFStack(3);
	int rightturns = 0;
	while ( rightturns <= 0 ) {
		
		int pt = p[row][col];
		
		rightturns=0; col=leftmost;
		while ( col > 0 && p[row][col-1] >= t ) col--;
		int srow = row;
		int scol = col;
		
		int direction = 0;
		int lastdirection = 0;
		int visits = 1;
		
		leaving->stacksize=0;
		borderpixels->stacksize=0;
		if ( SearchHoodDown2(row+1,col,p,pt,t,maxrow,maxcol)==0 ) {PushFStack(leaving,3);}
		if ( SearchHoodDown2(row,col+1,p,pt,t,maxrow,maxcol)==0 ) {PushFStack(leaving,2);}
		if ( SearchHoodDown2(row-1,col,p,pt,t,maxrow,maxcol)==0 ) {PushFStack(leaving,1);}

		do {
		
			if ( row>0 && row<maxrow-1 && col>0 && col<maxcol-1 ) PushPointStack(borderpixels,row,col);
			
			int done=1;
			pt=p[row][col];
			while ( done ) {
				direction = (direction+1) % 4;
				if ( direction==0 ) if (SearchHoodDown2(row,col-1,p,pt,t,maxrow,maxcol)==0) {done=0;col--;}
				if ( direction==1 ) if (SearchHoodDown2(row-1,col,p,pt,t,maxrow,maxcol)==0) {done=0;row--;}
				if ( direction==2 ) if (SearchHoodDown2(row,col+1,p,pt,t,maxrow,maxcol)==0) {done=0;col++;}
				if ( direction==3 ) if (SearchHoodDown2(row+1,col,p,pt,t,maxrow,maxcol)==0) {done=0;row++;}
			}

			if ( direction != lastdirection ) {
				if ( direction == (lastdirection+3)%4 ) { rightturns--; }
				else if ( direction == (lastdirection+1)%4 ) { rightturns++; }
					else { rightturns += 2; }
			}

			if ( row == srow && col == scol && (direction+2)%4 != PopFStack(leaving) ) visits = 0;		
			if ( row == srow && col < leftmost ) leftmost = col;
			lastdirection = direction;
			direction = (direction+2) % 4;
				
		} while ( visits );
	}
	FreeFStack(leaving);
}

void ResetMSERArray( MSERArray pa ) {
	if ( !MSERArrayGood(pa) ) return;
	int  *roots = pa->roots;
	int  *sizes = pa->sizes;
	char *flags = pa->flags;
	int k, max = pa->size;
	for (k=0;k<max;++k) sizes[k] = 1;
	for (k=0;k<max;++k) roots[k] = k;
	for (k=0;k<max;++k) flags[k] = 0;

}

MSERArray FreeMSERArray( MSERArray pa ) {
	if ( pa == NULL ) return NULL;
	if ( pa->sb+pa->minv != NULL )	free(pa->sb+pa->minv);
	if ( pa->sp != NULL )			free(pa->sp);
	if ( pa->roots != NULL )		free(pa->roots);
	if ( pa->sizes != NULL )		free(pa->sizes);
	if ( pa->flags != NULL )		free(pa->flags);
	if ( pa->regions != NULL )		free(pa->regions);
	free(pa);
	return NULL;
}

char MSERArrayGood( MSERArray array ) {
	if ( array == NULL ) return FALSE;
	if ( array->sizes == NULL ) return FALSE;
	if ( array->flags == NULL ) return FALSE;
	if ( array->roots == NULL ) return FALSE;
	if ( array->regions == NULL ) return FALSE;
	if ( array->sp == NULL ) return FALSE;
	if ( array->sb + array->minv == NULL ) return FALSE;
	return TRUE;
}

MSERArray ImageToMSERArray( Image image ) {
	
	if ( !ImageGood(image) ) return NULL;
	if ( !ImageRangeDefined(image) ) FindImageLimits(image);

	int maxrow   	= image->rows;
	int maxcol   	= image->cols;
	int maxv 		= image->maxv;
	int minv 		= image->minv;
	int arraymax 	= maxcol*maxrow;
	int maxr 		= maxrow - 2;
	int maxc 		= maxcol - 2;
	
	MSERArray mser = malloc(sizeof(struct MSERArraySt));
	if ( mser == NULL ) return FreeMSERArray(mser);
	
	mser->rows  = maxrow;
	mser->cols  = maxcol;
	mser->maxv  = maxv;
	mser->minv  = minv;
	mser->size  = arraymax;
	mser->image = image;

	mser->tvals 	= image->pixels[0];	
	mser->roots 	= malloc(arraymax*sizeof(int));
	mser->sizes 	= malloc(arraymax*sizeof(int));
	mser->flags 	= malloc(arraymax*sizeof(char));
	mser->regions 	= malloc(arraymax*sizeof(void *));
	mser->sp		= malloc(sizeof(int)*maxr*maxc);
	mser->sb		= ((int *)malloc(sizeof(int)*(maxv-minv+2))) - minv;
	
	if ( !MSERArrayGood(mser) ) return FreeMSERArray(mser);

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

