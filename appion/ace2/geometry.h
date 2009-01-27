#ifndef libcv_geometry
#define libcv_geometry

#include "cvtypes.h"
#include "Array.h"

void createDirectAffineTransform( f64 x1, f64 y1, f64 x2, f64 y2, f64 x3, f64 y3, f64 u1, f64 v1, f64 u2, f64 v2, f64 u3, f64 v3, f64 TR[3][3], f64 IT[3][3] );

f64 computeTriangleArea( f64 x1, f64 y1, f64 x2, f64 y2, f64 x3, f64 y3 );

#endif
