#include "defs.h"

int **AllocIMatrix(int rows, int cols, int ro, int co) {
    int i, **m, *v;
	m = (int **) malloc(rows * sizeof(int *));
	v = (int *)  malloc(rows * cols * sizeof(int));
	if ( m == NULL || v == NULL ) {
		if ( m != NULL ) free(m);
		if ( v != NULL ) free(v);
		return NULL;
	}
	memset(v,rows*cols*sizeof(int),0);
	m -= ro; v -= co;
	for (i=ro;i<rows+ro;i++) {
		m[i] = v;
		v += cols;
	}
	return m;
}

int **FreeIMatrix( int **matrix, int ro, int co ) {
	if ( matrix[ro]+co != NULL ) free(matrix[ro]+co);
	if ( matrix+ro != NULL ) free(matrix+ro);
	return NULL;
}

float **AllocFMatrix(int rows, int cols, int ro, int co) {
    int i;
    float **m, *v;	
	v = (float *)  malloc(rows * cols * sizeof(float));
    m = (float **) malloc(rows * sizeof(float *));
	if ( m == NULL || v == NULL ) {
		if ( m != NULL ) free(m);
		if ( v != NULL ) free(v);
		return NULL;
	}
	memset(v,rows*cols*sizeof(float),0);
	m -= ro; v -= co;
    for (i = ro; i < rows+ro; i++) {
		m[i] = v;
		v += cols;
    }
    return m;
}

float **FreeFMatrix( float **matrix, int ro, int co ) {
	if ( matrix[ro]+co != NULL ) free(matrix[ro]+co);
	if ( matrix+ro != NULL ) free(matrix+ro);
	return NULL;
}

double **AllocDMatrix(int rows, int cols, int ro, int co ) {
    int i;
    double **m, *v;
    m = (double **) malloc(rows*sizeof(double *));
    v = (double *)  malloc(rows*cols*sizeof(double));
	if ( m == NULL || v == NULL ) {
		FatalError("AllocDMatrix: Out of memory.\n");
		if ( m != NULL ) free(m);
		if ( v != NULL ) free(v);
		return NULL;
	}
	memset(v,rows*cols*sizeof(double),0);
	m -= ro; v -= co;
    for (i = ro; i < rows+ro; i++) {
		m[i] = v;
		v += cols;
    }
    return (m);
}

double **FreeDMatrix( double **matrix, int ro, int co ) {
	if ( matrix[ro]+co != NULL ) free(matrix[ro]+co);
	if ( matrix+ro != NULL ) free(matrix+ro);
	return NULL;
}

void CopyDMatrix( double **FROM, double **TO, int minr, int minc, int maxr, int maxc ) {
	if ( FROM == NULL || TO == NULL ) return;
	int row, col;
	for (row=minr;row<=maxr;row++) for(col=minc;col<=maxc;col++) TO[row][col] = FROM[row][col];
}

FArray NewFArray( int minrow, int mincol, int maxrow, int maxcol ) {
	
	FArray array = malloc(sizeof(struct FArraySt));
	if ( array == NULL ) return NULL;
	array->values = AllocFMatrix(maxrow-minrow+1, maxcol-mincol+1, minrow, mincol);
	array->maxrow  = maxrow;
	array->maxcol  = maxcol;
	array->minrow  = minrow;
	array->mincol  = mincol;
	array->rmaxrow = maxrow;
	array->rmaxcol = maxcol;
	array->rminrow = minrow;
	array->rmincol = mincol;
	
	if ( !FArrayGood(array) ) return FreeFArray(array);
	
	return array;
	
}

void SetFArray( FArray array, int row, int col, float val ) {
	
	if ( !FArrayGood(array) ) return;

	int maxrow = array->maxrow;
	int maxcol = array->maxcol;
	int minrow = array->minrow;
	int mincol = array->mincol;	
	
	if ( row <  minrow || col <  mincol || row > maxrow || col > maxcol ) {
		ResizeFArray( array, MIN(row,minrow), MIN(col,mincol), MAX(row,maxrow), MAX(col,maxcol) );
		if ( !FArrayGood(array) ) return;
	}
	
	array->values[row][col] = val;
	
}

float GetFArray( FArray array, int row, int col ) {
	if (row>=array->minrow && row<=array->maxrow && col>=array->mincol && col<=array->maxcol) return array->values[row][col];
	else return 0.0;
}

char FArrayGood( FArray array ) {
	if ( array == NULL ) return FALSE;
	if ( array->values == NULL ) return FALSE;
	if ( array->values[array->rminrow] == NULL ) return FALSE;
	return TRUE;
}

/* Function resizes the defined bounds of an array to the given bounds
	and if neccessary also resizes the memory block that stores the array
	values. When resizing the memory block a new size is chosen that finds
	a balance between space-effiency and reducing the potential of future
	memory resizing.  This saves time since memory resizing is expensive.  This
	function will never result in a reduced memory block size.  If this is your
	goal call the function FArrayCrunch() on your array instead. */

FArray ResizeFArray( FArray array, int nminr, int nminc, int nmaxr, int nmaxc ) {

	/* First we check the array */ 
	
	if ( !FArrayGood(array) ) return array;
	
	/* We store the current array bounds and memory bounds */
	
	int rmaxr = array->rmaxrow;
	int rmaxc = array->rmaxcol;
	int rminr = array->rminrow;
	int rminc = array->rmincol;
	int fmaxr = array->maxrow;
	int fmaxc = array->maxcol;
	int fminr = array->minrow;
	int fminc = array->mincol;
	

	/* The array WILL have the newly specified bounds */
	
	array->minrow = nminr;
	array->mincol = nminc;
	array->maxrow = nmaxr;
	array->maxcol = nmaxc;
	
	/* If the new bounds are within the allocated memory space we can return 
		without having to resize the memory block */

	if ( nminr >= rminr && nminc >= rminc && nmaxr <= rmaxr && nmaxc <= rmaxc ) return array;
		
	/* If the new bounds are outside the allocated memory space we must calculate new
		memory bounds.  We guess bounds in an attempt to reduce the number of
		future memory resizes. */
		
	/* We calculate bounds that are two times larger in every direction then the current bounds.
		This is done as shown to accomadate any potential mixture of positive and negative values */
		
	int xminr = rmaxr-2*(rmaxr-rminr);
	int xminc = rmaxc-2*(rmaxc-rminc);
	int xmaxr = rminr+2*(rmaxr-rminr);
	int xmaxc = rminc+2*(rmaxc-rminc);
	
	/* We then check each direction to find the ones in which the array is being expanded.  When
		this is the case we choose the larger of the two bounds, either the one specified by the
		user, or the one that is two times larger.  In this way we strike a balance between
		the times the function is called explicitly to set a new array size, or the times when it
		is being called to accomodate values that are being added, perhaps incrementally, outside
		the current bounds.  If the bounds are not being expanded we just use the old bounds */
		
	if ( nminr < rminr ) xminr = MIN(nminr,xminr);
	else xminr = rminr;
	if ( nminc < rminc ) xminc = MIN(nminc,xminc);
	else xminc = rminc;
	if ( nmaxr > rmaxr ) xmaxr = MAX(nmaxr,xmaxr);
	else xmaxr = rmaxr;
	if ( nmaxc > rmaxc ) xmaxc = MAX(nmaxc,xmaxc);
	else xmaxc = rmaxc;
	
	/* We go ahead and set our new memory bounds now */
	
	array->rmaxrow = xmaxr;
	array->rmaxcol = xmaxc;
	array->rminrow = xminr;
	array->rmincol = xminc;

	/* We allocate memory space for the new matrix and we create a pointer to the old memory location*/
	
	float **m2 = array->values;
	array->values = AllocFMatrix( xmaxr-xminr+1, xmaxc-xminc+1, xminr, xminc );

	/* We copy over the contents of the old memory block WITHIN the specified boundaries (not its memory
		boundaries).  The function we are calling finds the joint area of the specified bounds and the
		new bounds but does not do memory checking so the bounds given for m2 better be legitimate!!! */
	
	CopyCArrayIntoFArray(array,m2,fminr,fminc,fmaxr,fmaxc);
	
	/* We release the old memory block */
	
	FreeFMatrix(m2,rminr,rminc);
	
	return array;
	
}

int FArrayCols( FArray array ) {
	return array->maxcol - array->mincol + 1;
}

int FArrayRows( FArray array ) {
	return array->maxrow - array->minrow + 1;
}

void InitFArrayScalar( FArray array, float val ) {
	
	if ( !FArrayGood(array) ) return;
	
	int row,col;
	int minrow = array->minrow;
	int mincol = array->mincol;
	int maxrow = array->maxrow;
	int maxcol = array->maxcol;
	float **values = array->values;
	
	for (row=minrow;row<=maxrow;++row)
		for (col=mincol;col<=maxcol;++col)
			values[row][col] = val;
			
}

void CopyCArrayIntoFArray( FArray array, float **m, int lr, int lc, int rr, int rc ) {
	
	if ( !FArrayGood(array) ) return;
	
	int minrow = array->minrow;
	int mincol = array->mincol;
	int maxrow = array->maxrow;
	int maxcol = array->maxcol;
	
	minrow = MAX(minrow,lr);
	mincol = MAX(mincol,lc);
	maxrow = MIN(maxrow,rr);
	maxcol = MIN(maxcol,rc);
	
	int r, c;
	float **values = array->values;
	for (r=minrow;r<=maxrow;r++)
		for (c=mincol;c<=maxcol;c++)
			values[r][c] = m[r][c];
			
}

FArray FreeFArray( FArray array ) {
	FreeFMatrix( array->values, array->rminrow, array->rmincol );
	free( array );
	return NULL;
}

FVec NewFVec( int l, int r ) {
	FVec newvec = malloc(sizeof(struct FVecSt));
	if ( newvec == NULL ) return NULL;
	newvec->values = (float *)malloc(sizeof(float)*(r-l+1)) - l;
	newvec->l     = l;
	newvec->r     = r;
	newvec->max_l = l;
	newvec->max_r = r;
	if ( !FVecGood(newvec) ) return FreeFVec(newvec);
	memset(newvec->values+l,(r-l+1)*sizeof(int),0);
	return newvec;
}

char FVecGood( FVec vec ) {
	if ( vec == NULL ) return FALSE;
	if ( vec->values + vec->max_l == NULL ) return FALSE;
	if ( vec->r < vec->l ) return FALSE;
	if ( vec->max_r < vec->max_l ) return FALSE;
	return TRUE;
}

void SetFVec( FVec vec, int k, float val ) {
	if ( !FVecGood(vec) ) return;
	int l = vec->l;
	int r = vec->r;
	if ( k > r || k < l ) {
		ResizeFVec( vec, MIN(k,l), MAX(k,r) );
		if ( !FVecGood(vec) ) return;
	}
	vec->values[k] = val;
}

void ResizeFVec( FVec vec, int nl, int nr ) {
	
	if ( !FVecGood(vec) ) return;

	int fl = vec->l;
	int fr = vec->r;
	int ol = vec->max_l;
	int or = vec->max_r;
	
	vec->l = nl;
	vec->r = nr;
	
	/* If the modified bounds are within the assigned memory block do nothing */
	if ( nr <= or && nl >= ol ) return;
	
	/* We must assign a new memory block that can contain the new range.
		additionally we will make it larger by a factor of 2 to optimize
		for situations when values are being added to a vector in a 
		sequential fashion. */	
	
	int xr = fl + 2*(fr-fl);
	int xl = fr - 2*(fr-fl);	
	
	if ( nr > or ) xr = MAX(xr,nr);
	else xr = or;
	if ( nl < ol ) xl = MIN(xl,nl);
	else xl = ol;
	
	vec->max_r = xr;
	vec->max_l = xl;

	/* Assign the new location in memory */
	float *oldvals = vec->values;
	vec->values = (float *)malloc(sizeof(float)*(xr-xl+1)) - xl;
	
	/* Copy over the old values */
	CopyCArrayIntoFVec( vec, oldvals, fl, fr );

	/* Free the old memory block */
	free( oldvals + ol );
	
}

void CopyCArrayIntoFVec( FVec vec, float *v, int ol, int or ) {
	
	if ( !FVecGood(vec) ) return;
	
	int nr = vec->r;
	int nl = vec->l;
	
	nr = MIN(nr,or);
	nl = MAX(nl,ol);
	
	float *values = vec->values;
	
	while ( nl <= nr ) {
		values[nl] = v[nl];
		nl++;
	}

}

float GetFVec( FVec vec, int k ) {
	if (k<vec->l||k>vec->r||vec->values==NULL) return 0.0;
	else return vec->values[k];
}

FVec FreeFVec( FVec vec ) {
	if ( vec->values + vec->max_l != NULL ) free( vec->values + vec->max_l );
	free( vec );
	return NULL;
}	

PStack NewPStack(int size) {
	
	PStack stack = malloc(sizeof(struct PStackSt));
	stack->items = malloc(sizeof(void *)*size);
	stack->stacksize = 0;
	stack->realsize  = size;
	stack->cursor = 0;
	return stack;
	
}

void PushPStack( PStack stack, void *pointer ) {
	if ( pointer == NULL ) return;
	if ( stack->stacksize == stack->realsize ) {
		stack->realsize *= 2;
		void **newstack = malloc(sizeof(void *)*(stack->realsize));
		if ( newstack == NULL ) return;
		memcpy(newstack, stack->items, sizeof(void *)*stack->stacksize);
		free(stack->items);
		stack->items = newstack;
	}
	stack->items[stack->stacksize++] = pointer;
}

void *PopPStack( PStack stack ) {
	if (stack->stacksize == 0) return NULL;
	return stack->items[--(stack->stacksize)];
}	

PStack FreePStack( PStack stack ) {
	if ( stack->stacksize != 0 ) fprintf(stderr,"Stack is not empty, memory leak possible.\n");
	free(stack->items);
	free(stack);
	return NULL;	
}

char PStackEmpty( PStack stack ) {
	if ( stack == NULL ) return TRUE;
	if ( stack->stacksize == 0 ) return TRUE;
	return FALSE;
}

char PStackGood( PStack stack ) {
	if ( stack == NULL ) return FALSE;
	if ( stack->items == NULL ) return FALSE;
	return TRUE;
}

char PStackCycle( PStack stack ) {
	if ( stack->cursor >= stack->stacksize-1 ) {
		stack->cursor = 0;
		return 0;
	} return TRUE;
}

void *CyclePStack( PStack stack ) {
	return &(stack->items[stack->cursor++]);
} 

FStack NewFStack(int size) {
	
	FStack stack = malloc(sizeof(struct FStackSt));
	if ( stack == NULL ) return NULL;
	stack->items = malloc(sizeof(float *)*size);
	stack->stacksize = 0;
	stack->realsize  = size;
	
	return stack;
	
}

void PushFStack( FStack stack, float value ) {
	if ( stack->stacksize == stack->realsize ) {
		stack->realsize *= 2;
		float *newstack = malloc(sizeof(float)*(stack->realsize));
		if ( newstack == NULL ) return;
		int k;
		for (k=0;k<stack->stacksize;k++) newstack[k] = stack->items[k];
		free(stack->items);
		stack->items = newstack;
	}
	stack->items[stack->stacksize++] = value;	
}


float PopFStack( FStack stack ) {
	if (stack->stacksize==0) return 0;
	else return stack->items[--(stack->stacksize)];
}

char FStackEmpty( FStack stack ) {
	if ( stack->stacksize == 0 ) return 1;
	else return 0;
}

char FStackGood( FStack stack ) {
	if ( stack == NULL ) return FALSE;
	if ( stack->items == NULL ) return FALSE;
	else return TRUE;
}

void FreeFStack( FStack stack ) {
	if ( stack == NULL ) return;
	free(stack->items);
	free(stack);
}

PointStack NewPointStack( int size ) {
	PointStack pstack = malloc(sizeof(struct PointStackSt));
	if ( pstack == NULL ) return NULL;
	pstack->items     = malloc(sizeof(struct PointSt)*size);
	if ( pstack->items == NULL ) { free(pstack); return NULL; }
	pstack->realsize  = size;
	pstack->stacksize = 0;
	pstack->cursor    = 0;
	return pstack;
}
	
void PushPointStack( PointStack stack, int row, int col ) {
	if ( stack->stacksize == stack->realsize ) {
		stack->realsize *= 2;
		Point points = malloc(sizeof(struct PointSt)*(stack->realsize));
		memcpy(points, stack->items, sizeof(struct PointSt)*(stack->stacksize));
		free(stack->items);
		stack->items = points;
	}
	stack->items[stack->stacksize].row = row;
	stack->items[stack->stacksize].col = col;
	stack->stacksize++;
}

Point PopPointStack( PointStack stack ) {
	if ( stack->stacksize == 0 ) return NULL;
	else return &(stack->items[--stack->stacksize]);
}

void FreePointStack( PointStack stack ) {
	if ( stack == NULL ) return;
	free(stack->items);
	free(stack);
}

char PointStackEmpty( PointStack stack ) {
	if ( stack->stacksize == 0 ) return TRUE;
	else return FALSE;
}

int PointStackSize( PointStack stack ) {
	return stack->stacksize;
}

char PointStackCycle( PointStack stack ) {
	if ( stack->cursor == stack->stacksize ) {
		stack->cursor = 0;
		return FALSE;
	} else return TRUE;
}

PointStack CopyPointStack( PointStack stack ) {
	if ( !PointStackGood(stack) ) return NULL;
	PointStack copy = NewPointStack(stack->stacksize);
	if ( !PointStackGood(copy) ) return NULL;
	memcpy(copy->items,stack->items,sizeof(struct PointSt)*(stack->stacksize));
	copy->stacksize = stack->stacksize;
	copy->cursor    = stack->cursor;
	return copy;
}

Point CyclePointStack( PointStack stack ) {
	return &(stack->items[stack->cursor++]);
} 

char PointStackGood( PointStack stack ) {
	if ( stack == NULL ) return FALSE;
	if ( stack->items == NULL ) return FALSE;
	return TRUE;
}

IStack NewIStack( int size ) {
	IStack stack = malloc(sizeof(struct IStackSt));
	stack->items = malloc(sizeof(int)*size);
	stack->start = 0;
	stack->end   = 0;
	stack->size  = size;
	return stack;
}

void PushIStack( IStack stack, int value ) {
	stack->items[stack->end] = value;
	stack->end = (stack->end+1)%stack->size;
}

int PopIStack( IStack stack ) {
	int value = stack->items[stack->start];
	stack->start = (stack->start+1)%stack->size;
	return value;
}

