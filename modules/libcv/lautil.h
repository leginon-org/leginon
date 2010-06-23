
#ifndef libCV_lautil
#define libCV_lautil

#define SWAP(a,b) { temp=(a); (a)=(b); (b)=temp; }

char GaussJordanElimination( double **matrix, double **result, int size );
char InvertMatrix( double **matrix, int size );

char LUSolveMatrix( double **A, double **B, int m );
char LUDecomp( double **A, int n, int *index );
void LUSolveVec( double **LU, int n, int *index, double *b );

char SchurEigenVectors( double **T, double **Q, double **X_re, double **X_im, int m );
char SchurDecomposition( double **A, double **Q, int m);

char CholeskyDecomposition( double **A, int size );

/* Low level C array functions.  They do not check any values passed for
	correctness.  As a rule this means any passed pointer(s) must be addressable
	where specified. */
	
/* Copies the 'col' of the matrix 'mat' between the rows 'l' and 'r' into 'vec' */
void GETCOL( double **mat, int col, double *vec, int l, int r );
/* Copies the 'col' of the matrix 'mat' between the rows 'l' and 'r' into 'vec' */
void SETCOL( double **mat, int col, double *vec, int l, int r );
/* Multiplies the contents of 'vec' between 'l' and 'r' by 'scalar' */
void SVMLT( double scalar, double *vector, int l, int r );
/* Adds 'scalar' to the contents of 'vec' between 'l' and 'r' */
void SVADD( double scalar, double *v, int l, int r );
/* Sets 'vec' to zero between 'l' and 'r' */
void VZERO( double *vector, int l, int r );
/* Sets 'vec' between 'l' and 'r' to a random number*/
void VRAND( double *vector, int l, int r );
/* Returns the inner product between the arrays 'dp1' and 'dp2' between 'l' and 'r' */
double IP( double *dp1, double *dp2, int l, int r );
double VNORMINF( double *x, int l, int r );
void VLIMIT( double *v, int l, int r, double max, double min );
void MVMLT( double **A, double *b, double *out, int m);
double *VCOPY( double *in, double *out, int l, int r );
double *MLTADD( double *v1, double *v2, double s, int l, int r );
float VDISTSQ( float *d1, float *d2, int l, int r);
double VNORM2( double *x, int l, int r );

/* Higher level local functions used by the main functions */
void MAKEHQ( double **H, double *diag, double *beta, double **Qout, int m );
void ROTCOLS( double **mat, int i, int k, double c, double s, double **out, int m, int n);
void GIVENS( double x, double y, double *c, double *s);
void MAKEH( double **H, double **Hout, int m);
void HHTRVEC( double *hh, double beta, int i0, double *in, double *out, int m );
void HHLDR3(double x, double y, double z, double *nu1, double *beta, double *newval);
void ROTROWS( double **mat, int i, int k, double c, double s, double **out, int m, int n);
void HHLDR3ROWS(double **A, int k, int i0, double beta, double nu1, double nu2, double nu3, int m, int n);
void HHLDR3COLS(double **A, int k, int j0, double beta, double nu1, double nu2, double nu3, int m, int n);
void MATMULT( double **A, double **B, int r1, int c1, int r2, int c2 );


#endif
