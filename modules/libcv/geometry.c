
#include "geometry.h"
#include "util.h"
#include "lautil.h"
#include "mutil.h"
#include "image.h"

Ellipse NewEllipse( float Xc, float Yc, float Ma, float Mi, float phi ) {
	
	Ellipse newEllipse = malloc(sizeof(struct EllipseSt));
	if ( newEllipse == NULL ) return NULL;

	double A = 1.0/(Ma*Ma);
	double C = 1.0/(Mi*Mi);
	double c = cos(phi);
	double s = sin(phi);
	double A1 = A*c*c + C*s*s;
	double B1 = 2*c*s*(A-C);
	double C1 = A*s*s + C*c*c;
	double D1 = -2*A1*Xc - B1*Yc;
	double E1 = -2*C1*Yc - B1*Xc;
	double F1 = A1*Xc*Xc + B1*Yc*Xc + C1*Yc*Yc - 1;
	
	newEllipse->majorAxis = Ma;
	newEllipse->minorAxis = Mi;
	newEllipse->x	= Xc;
	newEllipse->y	= Yc;
	newEllipse->phi	= phi;
	newEllipse->A	= A1;
	newEllipse->B	= B1;
	newEllipse->C	= C1;
	newEllipse->D 	= D1;
	newEllipse->E	= E1;
	newEllipse->F	= F1; 

	double Pr = 4*A1*C1 - B1*B1;
	double Qr = 4*C1*D1 - 2*E1*B1;
	double Rr = 4*C1*F1 - E1*E1;
	newEllipse->bottomBound = (-Qr+sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);
	newEllipse->topBound    = (-Qr-sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);	
	Qr = 4*A1*E1 - 2*D1*B1;
	Rr = 4*A1*F1 - D1*D1;
	newEllipse->rightBound  = (-Qr+sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);
	newEllipse->leftBound   = (-Qr-sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);
	
	return newEllipse;
	
}

Point NewPoint( float x, float y, float z ) {
	Point newPoint = malloc(sizeof(struct PointSt));
	if ( newPoint == NULL ) return NULL;
	newPoint->x = x;
	newPoint->y = y;
	newPoint->z = z;
	return newPoint;
}

double **AddTranslationToAffineTransform( double **transform, float deltax, float deltay ) {
	if ( transform == NULL ) return NULL;
	transform[2][0] += deltax;
	transform[2][1] += deltay;
	return transform;
}

Polygon NewPolygon( int initialSize ) {
	Polygon poly = malloc(sizeof(struct PolygonSt));
	if ( poly == NULL ) return NULL;
	poly->vertices = malloc(sizeof(struct PointSt)*initialSize);
	if ( poly->vertices == NULL ) { free(poly); return NULL; }
	poly->memorySize  = initialSize;
	poly->numberOfVertices = 0;
	poly->cursor = 0;
	return poly;
}
	
void AddPolygonVertex( Polygon poly, float x, float y ) {
	if ( poly->numberOfVertices == poly->memorySize ) {
		poly->memorySize *= 2;
		Point newVertices = malloc(sizeof(struct PointSt)*(poly->memorySize));
		memcpy(newVertices, poly->vertices, sizeof(struct PointSt)*(poly->numberOfVertices));
		free(poly->vertices);
		poly->vertices = newVertices;
	}
	poly->vertices[poly->numberOfVertices].x = x;
	poly->vertices[poly->numberOfVertices].y = y;
	poly->numberOfVertices++;
}

Polygon FreePolygon( Polygon poly ) {
	if ( poly == NULL ) return NULL;
	if ( poly->vertices != NULL ) free(poly->vertices);
	free(poly);
	return NULL;
}

char PolygonHasVertices( Polygon poly ) {
	if ( poly->numberOfVertices == 0 ) return FALSE;
	else return TRUE;
}

int NumberOfPolygonVertices( Polygon poly ) {
	return poly->numberOfVertices;
}

Polygon CopyPolygon( Polygon poly ) {
	if ( !PolygonIsGood(poly) ) return NULL;
	Polygon copy = NewPolygon(poly->numberOfVertices);
	if ( !PolygonIsGood(copy) ) return NULL;
	memcpy(copy->vertices,poly->vertices,sizeof(struct PointSt)*(poly->numberOfVertices));
	copy->numberOfVertices = poly->numberOfVertices;
	copy->cursor = poly->cursor;
	return copy;
}

Point NextPolygonVertex( Polygon poly ) {
	if ( poly->cursor < poly->numberOfVertices ) return &(poly->vertices[poly->cursor++]);
	poly->cursor = 0;
	return NULL;
}

char PolygonIsGood( Polygon poly ) {
	if ( poly == NULL ) return FALSE;
	if ( poly->vertices == NULL ) return FALSE;
	return TRUE;
}

Ellipse CalculateEllipseFromPolygon( Polygon poly ) {

	int row, col, k;
	int size = poly->numberOfVertices;
	if ( size <= 10 ) {
		Debug(1,"CalculateEllipseFromPolygon:  Not enough points (10) for good fitting.\n");
		return NULL;
	}
	
	static double **Ep, **Q, **Ei, **S1, **S2, **S3, **T, **M, **E=NULL;
	static FArray D1, D2;
	if ( E == NULL ) {
		E  = AllocDMatrix(3,3,0,0);
		Ep = AllocDMatrix(3,3,0,0);
		Ei = AllocDMatrix(3,3,0,0);
		Q  = AllocDMatrix(3,3,0,0);
		D1 = NewFArray(0,0,2,0);
		D2 = NewFArray(0,0,2,0);
		T  = AllocDMatrix(3,3,0,0);
		M  = AllocDMatrix(3,3,0,0);
		S1 = AllocDMatrix(3,3,0,0);
		S2 = AllocDMatrix(3,3,0,0);
		S3 = AllocDMatrix(3,3,0,0);
	}
	
	//  The second step is to create the design matrix, which is split into two parts
	//  A quadratic part D1, and a linear part D2.
	
	ResizeFArray(D1,0,0,2,size-1);
	ResizeFArray(D2,0,0,2,size-1);	
	float **D1m = D1->values;
	float **D2m = D2->values;
	
	for (k=0;k<size;k++) {
		float x = poly->vertices[k].x;
		float y = poly->vertices[k].y;
		D1m[0][k] = x*x;
		D1m[1][k] = x*y;
		D1m[2][k] = y*y;
		D2m[0][k] = x;
		D2m[1][k] = y;
		D2m[2][k] = 1;
	}
	
	//  Now we produce the quadrants of the scatter matrix
	//  S1 = D1'*D1
	
	for (row=0;row<3;row++) {
		for (col=0;col<3;col++) {
			S1[row][col] = 0;
			for (k=0;k<size;k++) {
				S1[row][col] += (double)D1m[row][k]*(double)D1m[col][k];
	}}}
		
	//  S2 = D1'*D2
	for (row=0;row<3;row++) {
		for (col=0;col<3;col++) {
			S2[row][col] = 0;
			for (k=0;k<size;k++) {
				S2[row][col] += (double)D1m[row][k]*(double)D2m[col][k];
	}}}
	
	//  S3 = D2'*D2
	for (row=0;row<3;row++) {
		for (col=0;col<3;col++) {
			S3[row][col] = 0;
			for (k=0;k<size;k++) {
				S3[row][col] += (double)D2m[row][k]*(double)D2m[col][k];
	}}}
	
	//  We now have the three quadrants of our Scatter matrix, the fourth is simply
	//  the transpose of the second and does not need to be calculated.
	//  We now calculate the value of -S2 for solving S3*T = -S2'

	//  T = -S2'
	for (row=0;row<3;row++)
		for (col=0;col<3;col++)
			T[row][col] = -1*S2[col][row];
	
	if ( !LUSolveMatrix(S3,T,3) ) {
		Debug(1,"CalculateEllipseFromPolygon: Design matrix could not be inverted (Singular)\n");
		return NULL;
	}
	
	//   M = S1+S2*T
	for (row=0;row<3;row++) {
		for (col=0;col<3;col++) {
			M[row][col] = 0;
			for (k=0;k<3;k++) M[row][col] += S2[row][k]*T[k][col];
	}}
		
	for (row=0;row<3;row++)
		for (col=0;col<3;col++) 
			M[row][col] = S1[row][col] + M[row][col];

	// Now we pre-multiply the inv of the scatter matrix
	// M = M*Const [0 2 0; -1 0 0; 0 2 0]
	
	S1[0][0] =  M[2][0]/2;
	S1[1][1] = -M[1][1];
	S1[2][2] =  M[0][2]/2;
	S1[2][0] =  M[0][0]/2;
	S1[0][2] =  M[2][2]/2;
	S1[1][0] = -M[1][0];
	S1[0][1] =  M[2][1]/2;
	S1[2][1] =  M[0][1]/2;
	S1[1][2] = -M[1][2];
	
	for (row=0;row<9;row++) Ep[0][row] = S1[0][row];

	if ( !SchurDecomposition(Ep,Q,3) ) {
		Debug(1,"CalculateEllipseFromPolygon: Schur Decomposition Failed\n");
		return NULL;
	}
	if ( !SchurEigenVectors(Ep,Q,E,Ei,3) ) {
		Debug(1,"CalculateEllipseFromPolygon: Eigenvector Extraction Failed.\n");
		return NULL;
	}
	
	double cond[3];
	
	for (row=0;row<3;row++) 
		cond[row] = 4*E[0][row]*E[2][row]-E[1][row]*E[1][row];
	
	double e[6];
	for (col=0;col<3;col++) {
		if ( cond[col] >= 0 ) {
			e[0] = E[0][col];
			e[1] = E[1][col];
			e[2] = E[2][col];
			e[3] = e[0]*T[0][0]+e[1]*T[0][1]+e[2]*T[0][2];
			e[4] = e[0]*T[1][0]+e[1]*T[1][1]+e[2]*T[1][2];
			e[5] = e[0]*T[2][0]+e[1]*T[2][1]+e[2]*T[2][2];
		}
	}

	if ( e[0] < 0 ) for (col=0;col<6;col++) e[col] *= -1;
	double phi = atan(e[1]/(e[2]-e[0]))/2;
	
	double c = cos(phi);
	double s = sin(phi);
	
	char failed = FALSE;
	double Ad = e[0]*c*c - e[1]*c*s + e[2]*s*s; if ( ABS(Ad) < MACHEPS ) failed = TRUE;
	double Cd = e[0]*s*s + e[1]*s*c + e[2]*c*c; if ( ABS(Cd) < MACHEPS ) failed = TRUE;
	double Dd = e[3]*c - e[4]*s;                if ( ABS(Dd) < MACHEPS ) failed = TRUE;
	double Ed = e[3]*s + e[4]*c;                if ( ABS(Ed) < MACHEPS ) failed = TRUE;
	double Fd = e[5];                           if ( ABS(Fd) < MACHEPS ) failed = TRUE;
	
	if ( failed == TRUE ) {
		Debug(1,"CalculateEllipseFromPolygon: Ellipse parameters fell below machine accuracy.\n");
		return NULL;
	}

	double temp1 = -Dd/(2*Ad);
	double temp2 = -Ed/(2*Cd);
	double Xc =  c*temp1 + s*temp2;
	double Yc = -s*temp1 + c*temp2;
	double F  = -Fd + (Dd*Dd)/(4*Ad) + (Ed*Ed)/(4*Cd);
	double Ma  = sqrt(F/Ad);
	double Mi  = sqrt(F/Cd);
	
	phi = -phi;
	
	if ( Ma < Mi ) {
		phi = phi-SIGN(1,phi)*(PI/2);
		temp1 = Mi; Mi = Ma; Ma = temp1;
	}

	return NewEllipse(Xc,Yc,Ma,Mi,phi);
		
}

void CreateDirectAffineTransform( float x1, float y1, float x2, float y2, float x3, float y3, float u1, float v1, float u2, float v2, float u3, float v3, double **TR,
double **IT ) {

	if (IT != NULL ) {
		 double det = 1.0/(u1*(v2-v3)-v1*(u2-u3)+(u2*v3-u3*v2));
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
		double det = 1.0/(x1*(y2-y3)-y1*(x2-x3)+(x2*y3-x3*y2));
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

void ComputeEllipseTransform( Ellipse e1, Ellipse e2, double **TR, double **IT ) {

	float er1 = e1->x, ec1 = e1->y;
	float maj1 = e1->majorAxis;
	float min1 = e1->minorAxis;
	float c1 = cos(e1->phi), s1 = sin(e1->phi);
	float er2 = e2->x, ec2 = e2->y;
	float maj2 = e2->majorAxis;
	float min2 = e2->minorAxis;
	float c2 = cos(e2->phi), s2 = sin(e2->phi);
		
	float x1 = er1-min1*s1, y1 = ec1+min1*c1;
	float x2 = er1-maj1*c1, y2 = ec1-maj1*s1;
	float x3 = er1, y3 = ec1;
	float u1 = er2-min2*s2, v1 = ec2+min2*c2;
	float u2 = er2-maj2*c2, v2 = ec2-maj2*s2;
	float u3 = er2, v3 = ec2; 
	
	CreateDirectAffineTransform(x1,y1,x2,y2,x3,y3,u1,v1,u2,v2,u3,v3,TR,IT);
	
}	

char DecomposeAffineTransform( double **mat, double *tran ) {

	tran[XTRAN] = mat[2][0];
	tran[YTRAN] = mat[2][1];
	
	double p1x = mat[0][0];
	double p1y = mat[0][1];
	double p2x = mat[1][0];
	double p2y = mat[1][1];
	
	double length, dot;
	
 	/* Compute X scale factor and normalize first row. */
	length = sqrt( p1x * p1x + p1y * p1y );
 	tran[XSCALE] = length;
 	p1x = p1x / length;
	p1y = p1y / length;

 	/* Compute XY shear factor and make 2nd row orthogonal to 1st. */
 	dot = p1x * p2x + p1y * p2y;
	tran[XYSHEAR] = dot;
	p2x = p2x + p1x * tran[XYSHEAR];
	p2y = p2y + p1y * tran[XYSHEAR];

 	/* Now, compute Y scale and normalize 2nd row. */
 	length = sqrt( p2x * p2x + p2y * p2y );
	tran[YSCALE] = length;
	p2x = p2x / length;
	p2y = p2y / length;
 	tran[XYSHEAR] = tran[XYSHEAR] / tran[YSCALE];
	
 	tran[ROTATE] = atan2( p1y, p1x);
	
	fprintf(stderr,"Scaled by %f in X %f in Y, XY Shear is %f and rotation is %f translation is %f %f.\n",tran[XSCALE],tran[YSCALE],tran[XYSHEAR],tran[ROTATE]*DEG,tran[XTRAN],tran[YTRAN]);
		
 	return TRUE;
}

double **CalculateAffineFrameFromPolygon( Polygon poly ) {
	
	// The first step is to calculate the covariance matrix from the polygon vertices
	 
	int polygonSize = poly->numberOfVertices;
	
	double **A = AllocDMatrix(3,3,0,0);
	
	int i;
	double meanX = 0, meanY = 0;
	for (i=0;i<polygonSize;i++) meanX += poly->vertices[i].x;
	for (i=0;i<polygonSize;i++) meanY += poly->vertices[i].y;
	meanX /= polygonSize; meanY /= polygonSize;
	
	A[0][0] = 0.0;
	for (i=0;i<polygonSize;i++) A[0][0] += (double)poly->vertices[i].x * (double)poly->vertices[i].x;
	A[0][0] /= polygonSize;
	A[0][0] -= meanX*meanX;
	
	A[0][1] = 0.0;
	for (i=0;i<polygonSize;i++) A[0][1] += (double)poly->vertices[i].x * (double)poly->vertices[i].y;
	A[0][1] /= polygonSize;
	A[0][1] -= meanX*meanY;
	A[1][0] = A[0][1];
	
	A[1][1] = 0.0;
	for (i=0;i<polygonSize;i++) A[1][1] += (double)poly->vertices[i].y * (double)poly->vertices[i].y;
	A[1][1] /= polygonSize;
	A[1][1] -= meanY*meanY;
		
	// The next step is getting the covariance matrix in a form that can be used to affine normalize
	// the points.  This is performed by the Cholesky decomposition, referred to as taking the 'square-root' of the matrix
	
	CholeskyDecomposition( A, 2 );
	
	// Now we have a matrix that maps normalized points to their current position, we want the inverse so that
	// we can move the points to their normalized coordinates
	
	InvertMatrix( A, 2 );

	double scaleF = 1;
	
	A[0][0] *= scaleF; A[0][1] *= scaleF; A[0][2] = 0;
	A[1][0] *= scaleF; A[1][1] *= scaleF; A[1][2] = 0;

	float centX = meanX * A[0][0] + meanY * A[1][0];
	float centY = meanX * A[0][1] + meanY * A[1][1];
	
	A[2][0] = -centX; A[2][1] = -centY; A[2][2] = 1;
		
	return A;
	
}

float PointToLineDistance1( float x, float y, float slope, float intercept ) {
	float xa, ya;
	if ( slope == NaN ) {
		return ABS(x-intercept);
	} else if ( slope == 0.0 ) {
		return ABS(intercept-y);
	} else {
		ya = x*slope + intercept;
		xa = ( y - intercept ) / slope;
	}
	return PointToLineDistance2(x,ya,xa,y,x,y);
}

float PointToLineDistance2( float x1, float y1, float x2, float y2, float x3, float y3 ) {
	float det = -x2*y1 + x3*y1 + x1*y2 - x3*y2 - x1*y3 + x2*y3;
	if ( det == 0.0 ) return 0.0;
	float dist = sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1));
	return ( (ABS(det)) / dist );
}

void LineFit( float xVal, float yVal, float *a, float *b ) {
	
	static float sx = 0;
	static float sy = 0;
	static float sxx = 0;
	static float sxy = 0;
	static float size = 0;
	
	if ( xVal == yVal && xVal == NaN ) {
		sx = 0; sy = 0; sxx = 0; sxy = 0; size = 0;
		return;
	}
	
	sx += xVal;
	sy += yVal;
	sxx += xVal*xVal;
	sxy += xVal*yVal;
	size += 1;
	
	float delta = size*sxx - sx*sx;
	if ( delta == 0 ) {
		*a = NaN;
		*b = xVal;
	} else {
		*a = ( size*sxy - sx*sy ) / delta;
		*b = ( sxx*sy - sx*sxy ) / delta;
	}
	
}
	
float PolygonArea( Polygon points ) {

	int i, size = points->numberOfVertices;
	Point p = points->vertices;
	float sum1 = 0, sum2 = 0;
	
	for (i=0;i<size-1;i++) {
		sum1 += p[i].y * p[i+1].x;
		sum2 += p[i].x * p[i+1].y;
	}
	
	sum1 += p[size-1].y * p[0].x;
	sum2 += p[size-1].x * p[0].y;
	
	return 0.5 * ( sum1 - sum2 );
	
}

Polygon LinePolygonIntersection( Polygon poly, float x1, float y1, float x2, float y2 ) {
	int size = poly->numberOfVertices, i, k;
	float x3, y3, x4, y4, xInt, yInt;
	Polygon intersections = NewPolygon(10);
	for (i=0;i<size;i++) {
		x3 = poly->vertices[i].x;
		y3 = poly->vertices[i].y;
		k = ( i + 1 ) % size;
		x4 = poly->vertices[k].x;
		y4 = poly->vertices[k].y;
		k = LineLineIntersection( x1, y1, x2, y2, x3, y3, x4, y4, &xInt, &yInt );
		switch ( k ) {
			case 2: AddPolygonVertex(intersections,x3,y3);
					AddPolygonVertex(intersections,x4,y4);
					break;
			case 1: AddPolygonVertex(intersections,xInt,yInt);
			case 0: break;
		}
	}
	
	return intersections;
	
}
		
char LineLineIntersection( float x1, float y1, float x2, float y2, float x3, float y3, float x4, float y4, float *xint, float *yint ) {
	
	float aX = x2-x1;
	float bX = x3-x4;
	float x1Hi, x1Lo;
	if ( aX < 0 ) { x1Lo = x2; x1Hi = x1; }
	else { x1Hi = x2; x1Lo = x1; }
	if ( bX > 0 ) {
		if ( x1Hi < x4 || x3 < x1Lo ) return 0;
		else if ( x1Hi < x3 || x4 < x1Lo ) return 0;
	}
	
	float aY = y2-y1;
	float bY = y3-y4;
	float y1Hi, y1Lo;
	if ( aY < 0 ) { y1Lo = y2; y1Hi = y1; }
	else { y1Hi = y2; y1Lo = y1; }
	if ( bY > 0 ) {
		if ( y1Hi < y4 || y3 < y1Lo ) return 0;
		else if ( y1Hi < y3 || y4 < y1Lo ) return 0;
	}
	
	float cX = x1 - x3;
	float cY = y1 - y3;
	float d = bY * cX - bX * cY;
	float f = aY * bX - aX * bY;
	if ( f > 0 ) {
		if ( d < 0 || d > f ) return 0;
	} else {
		if ( d > 0 || d < f ) return 0;
	}
	
	float e = aX * cY - aY * cX;
	if ( f > 0 ) {
		if ( e < 0 || e > f ) return 0;
	} else {
		if ( e > 0 || e < f ) return 0;
	}
	
	if ( f == 0 ) return 2;
	
	float offset, num;
	num = d * aX;
	if ( num >= 0 && f >= 0 ) offset = f / 2;
	else offset = - f / 2;
	*xint = x1 + ( num + offset ) / f;
	num = d * aY;
	if ( num >= 0 && f >= 0 ) offset = f / 2;
	else offset = - f / 2;
	*yint = y1 + ( num + offset ) / f;
	
	return 1;
	
}
	
char PointInPolygon( Polygon poly, float x, float y ) {

      int i, j, c = 0;
	  int npol = poly->numberOfVertices;
	  Point p = poly->vertices;
      for ( i = 0, j = npol-1; i < npol; j = i++ ) {
	    if ((((p[i].y<=y) && (y<p[j].y)) || ((p[j].y<=y) && (y<p[i].y))) && (x < (p[j].x - p[i].x) * (y - p[i].y) / (p[j].y - p[i].y) + p[i].x)) c = !c;
      }
      return c;

}

Polygon PolygonLineReduction( Polygon poly, int minr, int maxr ) {
	
	int size = poly->numberOfVertices;
	FVec hist1 = FVecNew(0,size-1);
	
	int range, i, r, l;	
	float x1, y1, x2, y2, x3, y3;
	
	for (range=minr;range<=maxr;range++) {
		for (i=0;i<size;i++) {
		
			x2 = poly->vertices[i].x;
			y2 = poly->vertices[i].y;
		
			r = ( i + range ) % size;
			l = ( i + size - range ) % size;
		
			x1 = poly->vertices[l].x;
			y1 = poly->vertices[l].y;
			x3 = poly->vertices[r].x;
			y3 = poly->vertices[r].y;
		
			float dist = PointToLineDistance2(x1,y1,x3,y3,x2,y2);
			hist1->values[i] += dist;
			
		}
	}
	
	WrapGaussianBlur1D(hist1->values,hist1->l,hist1->r,5);
	FVecDivideBy(hist1,FVecMax(hist1));

	Polygon peaks = NewPolygon(10);
	
	for ( i = 0; i < size ; i++ ) {
		float peak = hist1->values[i];
		if ( peak < 0.3 ) continue;
		l = ( i + size - 1 ) % size;
		r = ( i + 1 ) % size;
		if ( hist1->values[r] > peak ) continue;
		if ( hist1->values[l] > peak ) continue;
		x1 = poly->vertices[i].x;
		y1 = poly->vertices[i].y;
		AddPolygonVertex(peaks,x1,y1);
	}
	
	size = peaks->numberOfVertices;
	for (i=0;i<size;i++) {
		r = ( i + 1 ) % size;
		x1 = peaks->vertices[i].x;
		y1 = peaks->vertices[i].y;
		x2 = peaks->vertices[r].x - x1;
		y2 = peaks->vertices[r].y - y1;
		float dist1 = sqrt( x2*x2 + y2*y2 );
		peaks->vertices[i].z = dist1;
	}
	
	FVecFree(hist1);
	
	return peaks;
	
}

float EvaluateVertexScore( Point p1, int l, int i, int r, float sc );
float EvaluateVertexScore( Point p1, int l, int i, int r, float sc ) {
	
	float x1 = p1[l].x;
	float y1 = p1[l].y;
	float x2 = p1[i].x;
	float y2 = p1[i].y;
	float x3 = p1[r].x;
	float y3 = p1[r].y;
	
	x1 = ( x2 - x1 ) * sc;
	y1 = ( y2 - y1 ) * sc;
	x3 = ( x3 - x2 ) * sc;
	y3 = ( y3 - y2 ) * sc;
	
	float l1 = sqrt(x1*x1+y1*y1);
	float l2 = sqrt(x3*x3+y3*y3);
	
	float turnAngle = acos((x1*x3+y1*y3)/(l1*l2));
	return ( turnAngle * l1 * l2 ) / ( l1 + l2 );

}

float EvaluateVertexScore2( Point p, int l, int i, int r );
float EvaluateVertexScore2( Point p, int l, int i, int r ) {
	
	int x1 = p[l].x;
	int y1 = p[l].y;
	int x2 = p[i].x;
	int y2 = p[i].y;
	int x3 = p[r].x;
	int y3 = p[r].y;
	
	if ( x1 == x3 && y1 == y3 ) return  0.5;
	else return ( y1*x2 + y2*x3 + y3*x1 - x1*y2 - x2*y3 - x3*y1 );
	
}
	
float EvaluateVertexScore3( Point p, int l, int i, int r );
float EvaluateVertexScore3( Point p, int l, int i, int r ) {
	
	int x1 = p[l].x;
	int y1 = p[l].y;
	int x2 = p[i].x;
	int y2 = p[i].y;
	int x3 = p[r].x;
	int y3 = p[r].y;
	
	return ( y1*x2 + y2*x3 + y3*x1 - x1*y2 - x2*y3 - x3*y1 );
	
}

float PolygonPerimeter( Polygon poly ) {
	int size = poly->numberOfVertices, i;
	float dist = 0;
	for (i=0;i<size;i++) {
		int r = ( i + 1 ) % size;
		float x1 = poly->vertices[i].x - poly->vertices[r].x;
		float y1 = poly->vertices[i].y - poly->vertices[r].y;
		dist += sqrt(x1*x1+y1*y1);
	}
	return dist;
}

void PolygonVertexEvolution( Polygon poly, float percent ) {
	
	int size = poly->numberOfVertices, i;
	int target = percent;
	if ( percent < 1 ) target = size * percent;
	
	Point p1 = poly->vertices;
	
	HeapQ vHeap = HeapQNew(size);
	int *lS = malloc(sizeof(int)*size);
	int *rS = malloc(sizeof(int)*size);
	int *iN = malloc(sizeof(int)*size);
	
	float length = 1.0 / size;

	for(i=0;i<size;i++) {
		lS[i] = ( i + size - 1 ) % size;
		rS[i] = ( i + 1 ) % size;
		iN[i] = 0;
		HeapQInsert( vHeap, i,  EvaluateVertexScore(p1,lS[i],i,rS[i],length) );
	}
	
	int newSize;
	for ( newSize = size ; newSize > target ; newSize-- ) {
		int m = HeapQDelMax( vHeap );
		int r = rS[m];
		int l = lS[m];
		rS[l] = r;
		lS[r] = l;
		HeapQChange( vHeap, r, EvaluateVertexScore(p1,lS[r],r,rS[r],length) );
		HeapQChange( vHeap, l, EvaluateVertexScore(p1,lS[l],l,rS[l],length) );
		iN[m] = 1;
	}
	
	int sSize = 0;
	for(i=0;i<size;i++) {
		if ( iN[i] == 1 ) continue;
		p1[sSize].x = p1[i].x;
		p1[sSize].y = p1[i].y;
		sSize++;
	}
	
	poly->numberOfVertices = sSize;
	
	free(iN); free(rS); free(lS); HeapQFree(vHeap);
	
}

void PolygonVertexClean( Polygon poly ) {
	
	int size = poly->numberOfVertices, i, r, l;
	Point p = poly->vertices;

	int *lS = malloc(sizeof(int)*size);
	int *rS = malloc(sizeof(int)*size);
	int *iN = malloc(sizeof(int)*size);
	int *oN = malloc(sizeof(int)*size);
	
	int sSize = 0;
	
	for(i=0;i<size;i++) {
		oN[i] = 1;
		lS[i] = ( i + size - 1 ) % size;
		rS[i] = ( i + 1 ) % size;
		if ( EvaluateVertexScore3(p,lS[i],i,rS[i]) == 0 ) iN[sSize++] = i;
	}
	
	while ( sSize > 0 ) {
		int m = iN[--sSize]; oN[m] = 0;
		r = rS[m], l = lS[m];
		rS[l] = r; lS[r] = l;
		if ( EvaluateVertexScore3(p,lS[l],l,r) == 0 ) iN[sSize++] = l;
		if ( EvaluateVertexScore3(p,l,r,rS[r]) == 0 ) iN[sSize++] = r;
	}
	
	for(i=0;i<size;i++) {
		if ( oN[i] == 0 ) continue;
		p[sSize].x = p[i].x;
		p[sSize].y = p[i].y;
		sSize++;
	}
	
	poly->numberOfVertices = sSize;

	free(iN); free(rS); free(lS); free(oN);
	
}

float PointToLineDistance( float x1, float y1, float x2, float y2, float x3, float y3 ) {
	float area2 = y1*x2 + y2*x3 + y3*x1 - x1*y2 - x2*y3 - x3*y1;
	float dist1 = sqrt( (x3-x2)*(x3-x2)+(y3-y2)*(y3-y2) );
	if ( dist1 == 0.0 ) return 0.0;
	return area2 / dist1;
}

char BoundTest( int l, int k, int r );
int **ConvexHull2D2( Polygon poly );

int PointToLineDistance3( Point p, int l, int i, int r ) {
	int x1 = p[l].x, y1 = p[l].y;
	int x2 = p[r].x, y2 = p[r].y;
	int x3 = p[i].x, y3 = p[i].y;
	float det = -x2*y1 + x3*y1 + x1*y2 - x3*y2 - x1*y3 + x2*y3;
	if ( det == 0.0 ) return 0.0;
	float dist = sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1));
	return ( (ABS(det)) / dist );
}

void DrawHull( Point p, int **hull, int size );

int PDist( Point p, int l, int r ) {
	int x = p[r].x - p[l].x;
	int y = p[r].y - p[l].y;
	return sqrt(x*x+y*y);
}

void PolygonACD( Polygon poly, float treshold, PStack stack ) {
	
	PolygonVertexClean( poly);
	
	fprintf(stderr,"Polygon Cleaned\n");
	
	int *sT = ConvexHull2D3( poly );
	
	sT[0] = 0;
	
	fprintf(stderr,"Convex Hull Found\n");
	
}

char BoundTest( int l, int k, int r ) {
	if ( l < r && ( k >= l && k <= r ) ) return TRUE;
	if ( l > r && ( k <= r || k >= l ) ) return TRUE;
	return FALSE;
}

int *ConvexHull2D3( Polygon poly ) {
	
	Debug(1,"Building Convex Hull: ");
	
	int size = poly->numberOfVertices;
	int i, k; Point p = poly->vertices;
	
	int *st = malloc(sizeof(int)*size), s = 0;
	
	int p1=0, p2=0, p3=0, p4=0;
	
	for (i=0;i<size;i++) {
		if ( p[p1].y > p[i].y ) p1 = i;
		if ( p[p2].x > p[i].x ) p2 = i;
		if ( p[p3].y < p[i].y ) p3 = i;
		if ( p[p4].x < p[i].x ) p4 = i; 
	}
	
	Debug(1,"Corners Found...");
	
	int *iD = malloc(sizeof(int)*(size+1));
	
	for (i=0,k=p1;i<=size;i++,k=(k+1)%size) iD[i] = k;
	
	Debug(1,"Offset Index Built...");
	
	st[0] = p4; st[1] = p1; s = 1;
	
	for (i=1;iD[i]!=p2;i++) {
		if ( EvaluateVertexScore3(p,st[s],iD[i],p2) > 0 ) {
			while ( EvaluateVertexScore3(p,st[s-1],st[s],iD[i]) <= 0 ) s--;
			st[++s] = iD[i];
		}
	}
	
	for (;iD[i]!=p3;i++) {
		if ( EvaluateVertexScore3(p,st[s],iD[i],p3) > 0 ) {
			while ( EvaluateVertexScore3(p,st[s-1],st[s],iD[i]) <= 0 ) s--;
			st[++s] = iD[i];
		}
	}
	
	for (;iD[i]!=p4;i++) {
		if ( EvaluateVertexScore3(p,st[s],iD[i],p4) > 0 ) {
			while ( EvaluateVertexScore3(p,st[s-1],st[s],iD[i]) <= 0 ) s--;
			st[++s] = iD[i];
		}
	}
	
	for (;iD[i]!=p1;i++) {
		if ( EvaluateVertexScore3(p,st[s],iD[i],p1) > 0 ) {
			while ( EvaluateVertexScore3(p,st[s-1],st[s],iD[i]) <= 0 ) s--;
			st[++s] = iD[i];
		}
	}
	
	st[++s] = p1;
	
	Debug(1,"Hull Has %d Vertices...DONE\n",s);
	
	free(iD);
	
	return st;
	
}


	
	
