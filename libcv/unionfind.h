
#ifndef libCV_unionfind
#define libCV_unionfind

typedef struct UnionFindTreeSt {
	int size;
	int *roots;
	int *sizes;
} *UnionFindTree;

UnionFindTree NewUnionFindTree( int size );
void ResetUnionFindTree( UnionFindTree tree );
int FindRootInTree( UnionFindTree tree, int node );
int FindRootInTreeAndCompressPath( UnionFindTree tree, int node );
int JoinNodesInTree( UnionFindTree tree, int node1, int node2 );

int Find( int *roots, int p );
int FindAndCompress( int *roots, int p );
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
