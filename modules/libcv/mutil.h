
#ifndef libCV_mutil
#define libCV_mutil

typedef struct FArraySt {
	float **values;
	int maxrow, maxcol;
	int minrow, mincol;
	int rmaxrow, rmaxcol;
	int rminrow, rmincol;
} *FArray;

typedef struct FVecSt {
	float *values;
	int max_r, max_l, r, l;
} *FVec;

typedef struct PStackSt {
	void **items;
	int stacksize, realsize, cursor;
} *PStack;

typedef struct FStackSt {
	float *items;
	int stacksize, realsize;
} *FStack;

typedef struct IStackSt {
	int *items, start, end, size;
} *IStack;

typedef struct HeapQSt {
	float *da;
	int *pq, *qp, N, rN;
} *HeapQ;

typedef struct RBNodeSt {
	float x;
	int idx;
	struct RBNodeSt *l;
	struct RBNodeSt *r;
	int N;
	char t;
} *RBNode;

typedef struct RBTreeSt {
	struct RBNodeSt *head;
	char id[256];
} *RBTree;

/* -----------------------------------------------------------------------------------------------------
	These are functions that deal with very basic two-dimensional memory structures that can be accessed
	as C arrays like so: example[row][col].  They support offsetting so that the array boundaries can be
	positive or negative.

	Allocate the simple matrices, AllocXMatrix():
	D is for double, F is for float, I is for int, and P is for pointer
	int rows = number of rows
	int cols = number of cols
	int ro   = row offset
	int co   = column offset
	Example: double **temp = AllocDMatrix(100,100,-50,-50);
		returns a double ** accessible from temp[-50][-50] to temp[50][50]

	
	Free the simple matrices, FreeXMatrix():
	D is for double, F is for float, I is for int, and P is for pointer
	**matrix = the pointer returned by AllocXMatrix()
	int ro	 = the row offset of the above matrix, you must keep track of this!
	int co   = the column offset of the above matrix, you must keep track of this!
	
	Copy the simple matrices, CopyXMatrix():
	**FROM	= the pointer of the source matrix
	**TO	= the pointer of the destination matrix, if NULL a new matrix is created
	minr	= minimum row index to start copy from
	minc 	= minimum column index to begin copy from
	maxr	= maximum row index to copy to
	maxc	= maximum column to copy to
	Note: if a new matrix is created as a result of passing NULL, the new matrix will ONLY
		be valid within the bounds given by minr, minc, maxr, maxc

*/

double **AllocDMatrix(int rows, int cols, int ro, int co );
float **AllocFMatrix(int rows, int cols, int ro, int co);
int **AllocIMatrix(int rows, int cols, int ro, int co);
void ***AllocPMatrix( int rows, int cols, int ro, int co );

double **FreeDMatrix( double **matrix, int ro, int co );
float **FreeFMatrix( float **matrix, int ro, int co );
int **FreeIMatrix( int **matrix, int ro, int co );
void ***FreePMatrix( int ***matrix, int ro, int co );

double **CopyDMatrix( double **FROM, double **TO, int minr, int minc, int maxr, int maxc );
float **CopyFMatrix( float **FROM, float **TO, int minr, int minc, int maxr, int maxc );
int **CopyIMatrix( int **FROM, int **TO, int minr, int minc, int maxr, int maxc );
void ***CopyPMatrix( int ***FROM, int ***TO, int minr, int minc, int maxr, int maxc );

/* -------------------------------------------------------------------------------------------------- */

/* -------------------------------------------------------------------------------------------------- */
/* FArrays are a very convenient, very nice way to work with two dimensional arrays.  They contain
	accessor functions to do boundary checks, and support soft and hard boundaries.  The soft
	boundaries indicate the desired array size, and the hard boundaries delimit actual memory
	bounds.  This allows FArrays to have elements added outside their bounds quickly and to be
	resized more efficiently. */
	 
/* Create a new FArray with bounds given by the passed variables */
FArray NewFArray( int minrow, int mincol, int maxrow, int maxcol );
/* Resize an FArray to a new set of soft boundaries.  While it may still be possible to access values
	outside the new soft boundaries this is not done to prevent segmentation faults */
FArray ResizeFArray( FArray array, int newminrow, int newmincol, int newmaxrow, int newmaxcol );
/* Set the value of the (row) and (col) of an FArray (array) to (val) */
void SetFArray( FArray array, int row, int col, float val );
/* Get the value of an FArray (array) at (row) and (col).  This accessor function prevents segmentation faults */
float GetFArray( FArray array, int row, int col );
/* Returns the number of columns in an FArray */
int FArrayCols( FArray array );
/* Returns the number of rows in an FArray */
int FArrayRows( FArray array );
/* Checks the condition of an FArray */
char FArrayIsGood( FArray array );
/* Sets all the values within an FArray to (val) */
void InitFArrayScalar( FArray array, float val );
/* Copies the values of a C array, such as allocted by AllocFMatrix() into an FArray between the bounds given */
FArray CopyCArrayIntoFArray( FArray array, float **m, int lr, int lc, int rr, int rc );
/* Free an FArray from memory */
FArray FreeFArray( FArray array );

/*----------------------------------------------------------------------------------------------------*/

FVec FVecNew( int l, int r );
void FVecSetAt( FVec vec, int k, float val );
void FVecAddAt( FVec vec, int pos, float val );
void FVecDivideBy( FVec vec, float val );
void FVecMultiplyBy( FVec vec, float val );
void FVecSet( FVec vec, float val );
float FVecMax( FVec vec );
float FVecMin( FVec vec );
float FVecStandardDeviation( FVec vec );
float FVecMean( FVec vec );
void FVecPrint( FVec vec );
float FVecGetAt( FVec vec, int k );
FVec FVecFree( FVec vec );
char FVecIsGood( FVec vec );
void CopyCArrayIntoFVec( FVec vec, float *v, int ol, int or );
void FVecResize( FVec vec, int nl, int nr );

PStack NewPStack(int size);
void PushPStack( PStack stack, void *pointer );
void *PopPStack( PStack stack );
char PStackIsEmpty( PStack stack );
PStack FreePStack( PStack stack );
char PStackCycle( PStack stack );
void *CyclePStack( PStack stack );

FStack NewFStack(int size);
void PushFStack( FStack stack, float value );
float PopFStack( FStack stack );
char PStackGood( PStack stack );
char FStackGood( FStack stack );
char FStackEmpty( FStack stack );
void FreeFStack( FStack stack );

IStack NewIStack( int size );
void PushIStack( IStack stack, int value );
int PopIStack( IStack stack );

char HeapQIsGood( HeapQ q );
HeapQ HeapQFree( HeapQ q );
HeapQ HeapQNew( int size );
void HeapQFixUp( HeapQ q, int k );
void HeapQFixDown( HeapQ q, int k );
void HeapQEx( int *qp, int *pq, int i, int j );
void HeapQInsert( HeapQ q, int k, float val );
int HeapQDelMax( HeapQ q );
void HeapQChange( HeapQ, int k, float val );
char HeapQLs( float *data, int k, int j );
float HeapQMax( HeapQ q );
int HeapQMaxIdx( HeapQ q );

#endif
