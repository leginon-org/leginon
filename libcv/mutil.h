
typedef struct FArraySt {
	float **values;
	int maxrow, maxcol;
	int minrow, mincol;
	int rmaxrow, rmaxcol;
	int rminrow, rmincol;
} *FArray;

typedef struct FVecSt {
	float * values;
	int maxr, minl, rmaxr, rminl;
} *FVec;

typedef struct PStackSt {
	void **items;
	int stacksize, realsize;
} *PStack;

typedef struct FStackSt {
	float *items;
	int stacksize, realsize;
} *FStack;

typedef struct IStackSt {
	int *items, start, end, size;
} *IStack;

typedef struct PointStackSt {
	struct PointSt *items;
	int stacksize;
	int realsize;
} *PointStack;

typedef struct PointSt {
	float row, col;
} *Point;

int **AllocIMatrix(int rows, int cols, int rowoffset, int coloffset);
void FreeIMatrix( int **matrix, int roff, int coff );
float **AllocFMatrix(int rows, int cols, int rowoffset, int coloffset);
void FreeFMatrix( float **matrix, int roff, int coff );
double **AllocDMatrix(int rows, int cols, int rowoffset, int coloffset);
void FreeDMatrix( double **matrix, int roff, int coff );

FArray NewFArray( int minrow, int mincol, int maxrow, int maxcol );
void ResizeFArray( FArray array, int newminrow, int newmincol, int newmaxrow, int newmaxcol );
void SetFArray( FArray array, int row, int col, float val );
float GetFArray( FArray array, int row, int col );
int FArrayCols( FArray array );
int FArrayRows( FArray array );
void InitFArray( FArray array, float val );
void FreeFArray( FArray array );

FVec NewFVec( int l, int r );
void SetFVec( FVec vec, int k, float val );
void ResizeVec( FVec vec, int newl, int newr );
float GetFVec( FVec vec, int k );
void FreeFVec( FVec vec );

PStack NewPStack(int size);
void PushPStack( PStack stack, void *pointer );
void *PopPStack( PStack stack );
char PStackEmpty( PStack stack );
void FreePStack( PStack stack );

FStack NewFStack(int size);
void PushFStack( FStack stack, float value );
float PopFStack( FStack stack );
char FStackEmpty( FStack stack );
void FreeFStack( FStack stack );

PointStack NewPointStack( int size );
void PushPointStack( PointStack stack, int row, int col );
Point PopPointStack( PointStack stack );
void FreePointStack( PointStack stack );

IStack NewIStack( int size );
void PushIStack( IStack stack, int value );
int PopIStack( IStack stack );
