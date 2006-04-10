#include "defs.h"
#include "ellipsefit.h"
#include "lautil.h"

Ellipse CalculateAffineEllipse( PointStack pixels, float scale ) {

	int row, col, k;
	int size = pixels->stacksize;
	if ( size <= 10 ) return NULL;
	
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
	
	/* We shift the pixel values over by 0.5 because we want an ellipse given in terms
		of real space, not pixel space.  This means if we're looking at pixel 0,0
		we aren't looking at position 0,0 but really position 0.5,0.5. */
	
	for (k=0;k<size;k++) {
		float x = pixels->items[k].row+0.5;
		float y = pixels->items[k].col+0.5;
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
	
	if ( !InvertMatrix(S3,T,3) ) return NULL;
	
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

	if ( !SchurDecomposition(Ep,Q,3) ) return NULL;
	if ( !SchurEigenVectors(Ep,Q,E,Ei,3) ) return NULL;

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
	
	double Ad = e[0]*c*c - e[1]*c*s + e[2]*s*s; if ( ABS(Ad) < MACHEPS ) return NULL;
	double Cd = e[0]*s*s + e[1]*s*c + e[2]*c*c; if ( ABS(Cd) < MACHEPS ) return NULL;
	double Dd = e[3]*c - e[4]*s;                if ( ABS(Dd) < MACHEPS ) return NULL;
	double Ed = e[3]*s + e[4]*c;                if ( ABS(Ed) < MACHEPS ) return NULL;
	double Fd = e[5];                           if ( ABS(Fd) < MACHEPS ) return NULL;

	double temp1 = -Dd/(2*Ad);
	double temp2 = -Ed/(2*Cd);
	double Xc =  c*temp1 + s*temp2;
	double Yc = -s*temp1 + c*temp2;
	double F  = -Fd + (Dd*Dd)/(4*Ad) + (Ed*Ed)/(4*Cd);
	double Ma  = sqrt(F/Ad)*scale;
	double Mi  = sqrt(F/Cd)*scale;
	
	phi = -phi;
	
	if ( Ma < Mi ) {
		phi = phi-SIGN(1,phi)*(PI/2);
		temp1 = Mi; Mi = Ma; Ma = temp1;
	}
	
	return NewEllipse(Xc,Yc,Ma,Mi,phi);
		
}

Ellipse NewEllipse( float Xc, float Yc, float Ma, float Mi, float phi ) {
	
	Ellipse e = malloc(sizeof(struct EllipseSt));
	if ( e == NULL ) return NULL;

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
	
	e->majaxis = Ma;
	e->minaxis = Mi;
	e->erow = Xc;
	e->ecol = Yc;
	e->phi = phi;
	e->A = A1;
	e->B = B1;
	e->C = C1;
	e->D = D1;
	e->E = E1;
	e->F = F1;

	double Pr = 4*A1*C1 - B1*B1;
	double Qr = 4*C1*D1 - 2*E1*B1;
	double Rr = 4*C1*F1 - E1*E1;
	e->maxr = (-Qr+sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr)+0.5;
	e->minr = (-Qr-sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);	
	Qr = 4*A1*E1 - 2*D1*B1;
	Rr = 4*A1*F1 - D1*D1;
	e->maxc = (-Qr+sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr)+0.5;
	e->minc = (-Qr-sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);
	
	return e;
	
}
