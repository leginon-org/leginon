
#ifndef libCV_mser
#define libCV_mser

#include "mutil.h"
#include "image.h"
#include "geometry.h"

typedef struct MSERArraySt {
	struct ImageSt *image;
	int maxv, minv, rows, cols, size;
	int *sp, *sb, maxbin;
	int *roots, *sizes, *tvals, *flags;
} *MSERArray;

typedef struct RegionSt {

	float row, col, ori, scale;
	
	double A,B,C,D,E,F,maj,min,phi;
	double minr, maxr, minc, maxc;
	
	struct ImageSt *image;
	
	struct PolygonSt *sizes;
	struct PolygonSt *border;
	int stable, root;
	
} *Region;

typedef struct TSizeSt {
	float size;
	float time;
	struct TSizeSt *next;
} *TSize;

char FindMSERegions( Image image, PStack Regions, float minsize, float maxsize, float minperiod, float minstable );

void ResetMSERArray( MSERArray pa );
MSERArray FreeMSERArray( MSERArray pa );
MSERArray ImageToMSERArray( Image image );
char MSERArrayIsGood( MSERArray array );

Region NewRegion( Ellipse e, Image im, Polygon vec, Polygon border, int stable, int region );

#endif
