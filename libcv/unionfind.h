
#ifndef libCV_unionfind
#define libCV_unionfind

typedef struct UnionFindSt {
	int size;
	int *roots;
	int *sizes;
} *UnionFind;

int Find( int *roots, int p );
int FindCompress( int *roots, int p );
int UnionFindB( int *roots, int *sizes, int a, int b );
int UnionFindA( int *roots, int *sizes, int a, int b );
int UnionFindAB( int *roots, int *sizes, int a, int b );
int Connect4( int *roots, int *sizes, int stride, int p );
int Connect8( int *roots, int *sizes, int stride, int p );
int Connect4Up( int *roots, int *sizes, int *tvals, int stride, int p, int t );
int Connect4Down( int *roots, int *sizes, int *tvals, int stride, int p, int t );
int Connect8Up( int *roots, int *sizes, int *tvals, int stride, int p, int t );
int Connect8Down( int *roots, int *sizes, int *tvals, int stride, int p, int t );

#endif
