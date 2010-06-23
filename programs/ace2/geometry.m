#include "geometry.h"

void createDirectAffineTransform( f64 x1, f64 y1, f64 x2, f64 y2, f64 x3, f64 y3, f64 u1, f64 v1, f64 u2, f64 v2, f64 u3, f64 v3, f64 TR[3][3], f64 IT[3][3] ) {

	if (IT != NULL ) {
		 f64 det = 1.0/(u1*(v2-v3)-v1*(u2-u3)+(u2*v3-u3*v2));
		 IT[0][0] = ((v2-v3)*x1+(v3-v1)*x2+(v1-v2)*x3)*det;
		 IT[0][1] = ((v2-v3)*y1+(v3-v1)*y2+(v1-v2)*y3)*det;
		 IT[0][2] = 0;
		 IT[1][0] = ((u3-u2)*x1+(u1-u3)*x2+(u2-u1)*x3)*det;
		 IT[1][1] = ((u3-u2)*y1+(u1-u3)*y2+(u2-u1)*y3)*det;
		 IT[1][2] = 0;
		 IT[2][0] = ((u2*v3-u3*v2)*x1+(u3*v1-u1*v3)*x2+(u1*v2-u2*v1)*x3)*det;
		 IT[2][1] = ((u2*v3-u3*v2)*y1+(u3*v1-u1*v3)*y2+(u1*v2-u2*v1)*y3)*det;
		 IT[2][2] = 1;
	}
	
	if (TR != NULL ) {
		f64 det = 1.0/(x1*(y2-y3)-y1*(x2-x3)+(x2*y3-x3*y2));
		TR[0][0] = ((y2-y3)*u1+(y3-y1)*u2+(y1-y2)*u3)*det;
		TR[0][1] = ((y2-y3)*v1+(y3-y1)*v2+(y1-y2)*v3)*det;
		TR[0][2] = 0;
		TR[1][0] = ((x3-x2)*u1+(x1-x3)*u2+(x2-x1)*u3)*det;
		TR[1][1] = ((x3-x2)*v1+(x1-x3)*v2+(x2-x1)*v3)*det;
		TR[1][2] = 0;
		TR[2][0] = ((x2*y3-x3*y2)*u1+(x3*y1-x1*y3)*u2+(x1*y2-x2*y1)*u3)*det;
		TR[2][1] = ((x2*y3-x3*y2)*v1+(x3*y1-x1*y3)*v2+(x1*y2-x2*y1)*v3)*det;
		TR[2][2] = 1;
		
	}

}

f64 computeTriangleArea( f64 x1, f64 y1, f64 x2, f64 y2, f64 x3, f64 y3 ) {
	return ( y1*x2 + y2*x3 + y3*x1 - x1*y2 - x2*y3 - x3*y1 );
}
