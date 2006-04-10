#include "unionfind.h"

int Find( int *roots, int p ) {
	while(p!=roots[p]) p=roots[p];
	return p;
}

int UnionFindB( int *roots, int *sizes, int a, int b ) {
	b=Find(roots,b);
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

int Connect4( int *roots, int *sizes, int stride, int p ) {
	int r = Find(roots,p);
	r = UnionFindB(roots,sizes,r,p-1);
	r = UnionFindB(roots,sizes,r,p+1);
	r = UnionFindB(roots,sizes,r,p-stride);
	r = UnionFindB(roots,sizes,r,p+stride);
	return r;
}

int Connect8(int *roots, int *sizes, int stride, int p ) {
	int r = Find(roots,p);
	r = UnionFindB(roots,sizes,r,p-1);
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
	int r = Find(roots,p);
	if ( tvals[p-1] >= t ) r = UnionFindB(roots,sizes,r,p-1);
	if ( tvals[p+1] >= t ) r = UnionFindB(roots,sizes,r,p+1);
	if ( tvals[p-stride] >= t ) r = UnionFindB(roots,sizes,r,p-stride);
	if ( tvals[p+stride] >= t ) r = UnionFindB(roots,sizes,r,p+stride);
	return r;
}

int Connect4Down( int *roots, int *sizes, int *tvals, int stride, int p, int t ) {
	int r = Find(roots,p);
	if ( tvals[p-1] <= t ) r = UnionFindB(roots,sizes,r,p-1);
	if ( tvals[p+1] <= t ) r = UnionFindB(roots,sizes,r,p+1);
	if ( tvals[p-stride] <= t ) r = UnionFindB(roots,sizes,r,p-stride);
	if ( tvals[p+stride] <= t ) r = UnionFindB(roots,sizes,r,p+stride);
	return r;
}

int Connect8Up( int *roots, int *sizes, int *tvals, int stride, int p, int t ) {
	int r = Find(roots,p);
	if ( tvals[p-1] >= t ) r = UnionFindB(roots,sizes,r,p-1);
	if ( tvals[p+1] >= t ) r = UnionFindB(roots,sizes,r,p+1);
	if ( tvals[p-stride] >= t ) r = UnionFindB(roots,sizes,r,p-stride);
	if ( tvals[p+stride] >= t ) r = UnionFindB(roots,sizes,r,p+stride);
	if ( tvals[p+stride-1] >= t ) r = UnionFindB(roots,sizes,r,p+stride-1);
	if ( tvals[p+stride+1] >= t ) r = UnionFindB(roots,sizes,r,p+stride+1);
	if ( tvals[p-stride-1] >= t ) r = UnionFindB(roots,sizes,r,p-stride-1);
	if ( tvals[p-stride+1] >= t ) r = UnionFindB(roots,sizes,r,p-stride+1);
	return r;
}

int Connect8Down( int *roots, int *sizes, int *tvals, int stride, int p, int t ) {
	int r = Find(roots,p);
	if ( tvals[p-1] <= t ) r = UnionFindB(roots,sizes,r,p-1);
	if ( tvals[p+1] <= t ) r = UnionFindB(roots,sizes,r,p+1);
	if ( tvals[p-stride] <= t ) r = UnionFindB(roots,sizes,r,p-stride);
	if ( tvals[p+stride] <= t ) r = UnionFindB(roots,sizes,r,p+stride);
	if ( tvals[p+stride-1] <= t ) r = UnionFindB(roots,sizes,r,p+stride-1);
	if ( tvals[p+stride+1] <= t ) r = UnionFindB(roots,sizes,r,p+stride+1);
	if ( tvals[p-stride-1] <= t ) r = UnionFindB(roots,sizes,r,p-stride-1);
	if ( tvals[p-stride+1] <= t ) r = UnionFindB(roots,sizes,r,p-stride+1);
	return r;
}
