#include "unionfind.h"
#include "util.h"

UnionFindTree NewUnionFindTree( int size ) {
	UnionFindTree newTree = malloc(sizeof(struct UnionFindTreeSt));
	if ( newTree == NULL ) return newTree;
	newTree->roots = malloc(sizeof(int)*size);
	newTree->sizes = malloc(sizeof(int)*size);
	newTree->size  = size;
	return newTree;
}

void ResetUnionFindTree( UnionFindTree tree ) {
	int i;
	for ( i=0;i<tree->size;i++ ) {
		tree->sizes[i] = 1;
		tree->roots[i] = i;
	}
}

int FindRootInTree( UnionFindTree tree, int node ) {
	while ( node != tree->roots[node] ) node = tree->roots[node];
	return node;
}

int FindRootInTreeAndCompressPath( UnionFindTree tree, int node ) {
	while ( node != tree->roots[node] ) {
		tree->roots[node] = tree->roots[tree->roots[node]];
		node = tree->roots[node];
	}
	return node;
}

int JoinNodesInTree( UnionFindTree tree, int node1, int node2 ) {
	node1 = FindRootInTreeAndCompressPath( tree, node1 );
	node2 = FindRootInTreeAndCompressPath( tree, node2 );
	if ( node1 == node2 ) return node1;
	if ( tree->sizes[node2] <= tree->sizes[node1] ) {
		tree->roots[node2] = tree->roots[node1];
		tree->sizes[node1] += tree->sizes[node2];
		return node1;
	} else {
		tree->roots[node1] = tree->roots[node2];
		tree->sizes[node2] += tree->sizes[node1];
		return node2;
	}
}
	

int Find( int *roots, int p ) {
	while( p != roots[p] ) p = roots[p];
	return p;
}

int FindAndCompress( int *roots, int p ) {
	while ( p != roots[p] ) {
		roots[p] = roots[roots[p]];
		p = roots[p];
	}
	return p;
}

int UnionFindB( int *roots, int *sizes, int a, int b ) {
	b = FindAndCompress(roots,b);
	if ( b == a ) return a;
	if ( sizes[b] <= sizes[a] ) {
		roots[b]=a;
		sizes[a]+=sizes[b];
		return a;
	} else {
		roots[a]=b;
		sizes[b]+=sizes[a];
		return b;
	}
}

int UnionFindA( int *roots, int *sizes, int a, int b ) {
	a = FindAndCompress(roots,a);
	if ( b == a ) return a;
	if ( sizes[b] <= sizes[a] ) {
		roots[b] = a;
		sizes[a] += sizes[b];
		return a;
	} else {
		roots[a] = b;
		sizes[b] += sizes[a];
		return b;
	}
}

int UnionFindAB( int *roots, int *sizes, int a, int b ) {
	a = FindAndCompress(roots,a);
	b = FindAndCompress(roots,b);
	if ( b == a ) return a;
	if ( sizes[b] <= sizes[a] ) {
		roots[b] = a;
		sizes[a] += sizes[b];
		return a;
	} else {
		roots[a] = b;
		sizes[b] += sizes[a];
		return b;
	}
}

int Connect4( int *roots, int *sizes, int stride, int p ) {
	int r = p;
	r = UnionFindAB(roots,sizes,r,p-1);
	r = UnionFindB(roots,sizes,r,p+1);
	r = UnionFindB(roots,sizes,r,p-stride);
	r = UnionFindB(roots,sizes,r,p+stride);
	return r;
}

int Connect8(int *roots, int *sizes, int stride, int p ) {
	int r = p;
	r = UnionFindAB(roots,sizes,r,p-1);
	r = UnionFindB(roots,sizes,r,p+1);
	r = UnionFindB(roots,sizes,r,p-stride);
	r = UnionFindB(roots,sizes,r,p+stride);
	r = UnionFindB(roots,sizes,r,p+stride-1);
	r = UnionFindB(roots,sizes,r,p+stride+1);
	r = UnionFindB(roots,sizes,r,p-stride-1);
	r = UnionFindB(roots,sizes,r,p-stride+1);
	return r;
}

int Connect4Up( int *roots, int *sizes, int *tvals, int stride, int p, int t ) {
	int r = FindAndCompress(roots,p);
	if ( tvals[p-1] <= t ) 		r = UnionFindB(roots,sizes,r,p-1);
	if ( tvals[p+1] <= t ) 		r = UnionFindB(roots,sizes,r,p+1);
	if ( tvals[p-stride] <= t ) r = UnionFindB(roots,sizes,r,p-stride);
	if ( tvals[p+stride] <= t ) r = UnionFindB(roots,sizes,r,p+stride);
	return r;
}

int Connect4Down( int *roots, int *sizes, int *tvals, int stride, int p, int t ) {
	int r = FindAndCompress(roots,p);
	if ( tvals[p-1] >= t )		r = UnionFindB(roots,sizes,r,p-1);
	if ( tvals[p+1] >= t )		r = UnionFindB(roots,sizes,r,p+1);
	if ( tvals[p-stride] >= t )	r = UnionFindB(roots,sizes,r,p-stride);
	if ( tvals[p+stride] >= t )	r = UnionFindB(roots,sizes,r,p+stride);
	return r;
}

int Connect8Up( int *roots, int *sizes, int *tvals, int stride, int p, int t ) {
	int r = FindAndCompress(roots,p);
	if ( tvals[p-1] >= t )			r = UnionFindB(roots,sizes,r,p-1);
	if ( tvals[p+1] >= t )			r = UnionFindB(roots,sizes,r,p+1);
	if ( tvals[p-stride] >= t )		r = UnionFindB(roots,sizes,r,p-stride);
	if ( tvals[p+stride] >= t )		r = UnionFindB(roots,sizes,r,p+stride);
	if ( tvals[p+stride-1] >= t )	r = UnionFindB(roots,sizes,r,p+stride-1);
	if ( tvals[p+stride+1] >= t )	r = UnionFindB(roots,sizes,r,p+stride+1);
	if ( tvals[p-stride-1] >= t )	r = UnionFindB(roots,sizes,r,p-stride-1);
	if ( tvals[p-stride+1] >= t )	r = UnionFindB(roots,sizes,r,p-stride+1);
	return r;
}

int Connect8Down( int *roots, int *sizes, int *tvals, int stride, int p, int t ) {
	int r = FindAndCompress(roots,p);
	if ( tvals[p-1] <= t )			r = UnionFindB(roots,sizes,r,p-1);
	if ( tvals[p+1] <= t )			r = UnionFindB(roots,sizes,r,p+1);
	if ( tvals[p-stride] <= t )		r = UnionFindB(roots,sizes,r,p-stride);
	if ( tvals[p+stride] <= t )		r = UnionFindB(roots,sizes,r,p+stride);
	if ( tvals[p+stride-1] <= t )	r = UnionFindB(roots,sizes,r,p+stride-1);
	if ( tvals[p+stride+1] <= t )	r = UnionFindB(roots,sizes,r,p+stride+1);
	if ( tvals[p-stride-1] <= t )	r = UnionFindB(roots,sizes,r,p-stride-1);
	if ( tvals[p-stride+1] <= t )	r = UnionFindB(roots,sizes,r,p-stride+1);
	return r;
}
