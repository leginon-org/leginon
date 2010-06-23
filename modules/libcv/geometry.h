
#ifndef libCV_geometry
#define libCV_geometry

#include "mutil.h"

typedef struct PolygonSt {
	struct PointSt *vertices;
	int numberOfVertices, memorySize, cursor;
} PolygonSt;
typedef PolygonSt *Polygon;

typedef struct PointSt {
	float x, y, z;
} PointSt;
typedef PointSt *Point;

typedef struct EllipseSt {
	double x, y, majorAxis, minorAxis, phi;
	double A,B,C,D,E,F;
	double topBound, bottomBound, leftBound, rightBound;
} EllipseSt;
typedef EllipseSt *Ellipse;

enum affineindices {
	XTRAN,
	YTRAN,
	XSCALE,
	YSCALE,
	XYSHEAR,
	ROTATE,
};

Ellipse NewEllipse( float Xc, float Yc, float A, float B, float phi );

Polygon	NewPolygon( int numberOfVertices );
void AddPolygonVertex( Polygon poly, float x, float y );
Polygon FreePolygon( Polygon poly );
char PolygonHasVertices( Polygon poly );
int NumberOfPolygonVertices( Polygon poly );
Polygon CopyPolygon( Polygon poly );
Point NextPolygonVertex( Polygon poly );
char PolygonIsGood( Polygon poly );

Point NewPoint( float x, float y, float z );

Ellipse CalculateEllipseFromPolygon( Polygon poly );
double **CalculateAffineFrameFromPolygon( Polygon poly );

float PointToLineDistance1( float x, float y, float slope, float intercept );
float PointToLineDistance2( float x1, float y1, float x2, float y2, float x3, float y3 );
void LineFit( float xVal, float yVal, float *a, float *b );
float PolygonArea( Polygon points );
void ComputeEllipseTransform( Ellipse e1, Ellipse e2, double **TR, double **IT );
char LineLineIntersection( float x1, float y1, float x2, float y2, float x3, float y3, float x4, float y4, float *xint, float *yint );
void CreateDirectAffineTransform( float x1, float y1, float x2, float y2, float x3, float y3, float u1, float v1, float u2, float v2, float u3, float v3, double **TR,
double **IT );

char DecomposeAffineTransform( double **mat, double *tran );
Polygon LinePolygonIntersection( Polygon poly, float x1, float y1, float x2, float y2 );
char PointInPolygon( Polygon poly, float x, float y );
Polygon PolygonLineReduction( Polygon poly, int minr, int maxr );
void PolygonVertexEvolution( Polygon poly, float percent );
void PolygonACD( Polygon poly, float treshold, PStack stack );
int *ConvexHull2D( Polygon p );
int *ConvexHull2D3( Polygon poly );

#endif
