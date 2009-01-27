#include "Ellipse.h"

@implementation Ellipse

+(id) newAtX:(f64)xc andY:(f64)yc withXAxis:(f64)xa andYAxis:(f64)ya rotatedBy:(f64)phi {
	
	/* NewEllipse Function
	   Creates an ellipse structure, and converts the passed parameters to general conic parameters
	   Xc, Yc = The x and y coordinates of the ellipse center
	   Ma, Mi = The length of the major and minor ellipse axis
	   phi    = The rotation in radians of the minor axis from the x (horizontal) axis, + is ccw
	*/

	EllipseP new_ellipse = [[Ellipse alloc] init];
	if ( new_ellipse == nil ) return nil;
	[new_ellipse setX_axis:xa y_axis:ya x_center:xc y_center:yc rotation:phi];
	return new_ellipse;
	
}

+(id) newWithA:(f64)a b:(f64)b c:(f64)c d:(f64)d e:(f64)e f:(f64)f {
	
	
	EllipseP new_ellipse = [[Ellipse alloc] init];
	if ( new_ellipse == nil ) return nil;
	[new_ellipse setGeneralA:a B:b C:c D:d E:e F:f];
	return new_ellipse;
	
}

+(id) newFromPoints:(ArrayP)points {
	
	u32 size = [points sizeOfDimension: 0];
	u32 k;
	int signum;
	f64 TR_c[9], EV_c[9], cond[3], e[6];
	f64 * X1, * X2, * X3;
	gsl_complex * X4;
	
	// We build the linear and non-linear portions of the ellipse parameters
	
	u32 ellipse_size_max = 0;
	f64 * D1_r = NEWV(f64,size*3);
	f64 * D2_r = NEWV(f64,size*3);
	gsl_matrix * EP_g = gsl_matrix_alloc(3,3);
	gsl_matrix * S1_g = gsl_matrix_alloc(3,3);
	gsl_matrix * S2_g = gsl_matrix_alloc(3,3);
	gsl_matrix * S3_g = gsl_matrix_alloc(3,3);
	gsl_matrix * TR_g = gsl_matrix_alloc(3,3);
	gsl_matrix * MI_g = gsl_matrix_alloc(3,3);
	gsl_vector * V1_g = gsl_vector_alloc(3);
	gsl_permutation * P1_g = gsl_permutation_alloc(3);
	gsl_vector_complex * EX_g = gsl_vector_complex_alloc(3);
	gsl_matrix_complex * EV_g = gsl_matrix_complex_alloc(3,3);
	gsl_eigen_nonsymmv_workspace * W1_g = gsl_eigen_nonsymmv_alloc(3);
	
	f64 * data = [points data];
	
//	fprintf(stderr,"Creating Design Matrices D1 and D2\n");
	
	for (k=0;k<size;k++) {
		f64 x = data[k*2];
		f64 y = data[k*2+1];
		printf("%f %f\n",x,y);
		D1_r[k] = x * x;
		D1_r[k+size] = x * y;
		D1_r[k+size+size] = y * y;
		D2_r[k] = x;
		D2_r[k+size] = y;
		D2_r[k+size+size] = 1;
	}
	
	//  Now we produce the quadrants of the scatter matrix
	//  S1 = D1'*D1, S2 = D1'*D2, S3 = D2'*D2, S4 = S2;

//	fprintf(stderr,"Creating Scatter Matrices S1, S2 and S3\n");
	
	gsl_matrix_view D1_g = gsl_matrix_view_array(D1_r,3,size);
	gsl_matrix_view D2_g = gsl_matrix_view_array(D2_r,3,size);
	
	gsl_blas_dgemm(CblasNoTrans,CblasTrans,1.0,&D1_g.matrix,&D1_g.matrix,0.0,S1_g);
	gsl_blas_dgemm(CblasNoTrans,CblasTrans,1.0,&D1_g.matrix,&D2_g.matrix,0.0,S2_g);
	gsl_blas_dgemm(CblasNoTrans,CblasTrans,1.0,&D2_g.matrix,&D2_g.matrix,0.0,S3_g);
	
//	fprintf(stderr,"S1:\n");
//	X2 = gsl_matrix_ptr(S1_g,0,0);
//	fprintf(stderr,"%e %e %e\n",X2[0],X2[1],X2[2]);
//	fprintf(stderr,"%e %e %e\n",X2[3],X2[4],X2[5]);
//	fprintf(stderr,"%e %e %e\n",X2[6],X2[7],X2[8]);
	
//	fprintf(stderr,"S2:\n");
//	X2 = gsl_matrix_ptr(S2_g,0,0);	
//	fprintf(stderr,"%e %e %e\n",X2[0],X2[1],X2[2]);
//	fprintf(stderr,"%e %e %e\n",X2[3],X2[4],X2[5]);
//	fprintf(stderr,"%e %e %e\n",X2[6],X2[7],X2[8]);
	
//	fprintf(stderr,"S3:\n");
//	X2 = gsl_matrix_ptr(S3_g,0,0);	
//	fprintf(stderr,"%e %e %e\n",X2[0],X2[1],X2[2]);
//	fprintf(stderr,"%e %e %e\n",X2[3],X2[4],X2[5]);
//	fprintf(stderr,"%e %e %e\n",X2[6],X2[7],X2[8]);

	//  We now have the three quadrants of our Scatter matrix, the fourth is simply
	//  the transpose of the second and does not need to be calculated.
	//  We now solve S3 * TR = -S2' for TR, TR begins as -S2' and ends as the solution
	
	gsl_linalg_LU_decomp(S3_g,P1_g,&signum);
	gsl_linalg_LU_invert(S3_g,P1_g,MI_g);
	gsl_blas_dgemm(CblasNoTrans,CblasTrans,-1.0,MI_g,S2_g,0.0,TR_g);

//	fprintf(stderr,"TR:\n");
//	X2 = gsl_matrix_ptr(TR_g,0,0);
//	fprintf(stderr,"%e %e %e\n",X2[0],X2[1],X2[2]);
//	fprintf(stderr,"%e %e %e\n",X2[3],X2[4],X2[5]);
//	fprintf(stderr,"%e %e %e\n",X2[6],X2[7],X2[8]);
	
	//   MI = S1 + S2 * TR

	gsl_matrix_memcpy(MI_g,S1_g);
	gsl_blas_dgemm(CblasNoTrans,CblasNoTrans,1.0,S2_g,TR_g,1.0,MI_g);
	
	// Now we pre-multiply the inv of the scatter matrix
	// EP = MI * Const [0 2 0; -1 0 0; 0 2 0]
	
//	fprintf(stderr,"M = S1 + S2*TR\n");
//	X2 = gsl_matrix_ptr(MI_g,0,0);
//	fprintf(stderr,"%e %e %e\n",X2[0],X2[1],X2[2]);
//	fprintf(stderr,"%e %e %e\n",X2[3],X2[4],X2[5]);
//	fprintf(stderr,"%e %e %e\n",X2[6],X2[7],X2[8]);
	
	gsl_matrix_memcpy(EP_g,MI_g);
	X1 = gsl_matrix_ptr(EP_g,0,0);
	X2 = gsl_matrix_ptr(MI_g,0,0);
	
	X2[3] = X1[3];
	X2[4] = X1[4];
	X2[5] = X1[5];
	X2[0] = -X1[6] / 2.0;
	X2[1] = -X1[7] / 2.0;
	X2[2] = -X1[8] / 2.0;
	X2[6] = -X1[0] / 2.0;
	X2[7] = -X1[1] / 2.0;
	X2[8] = -X1[2] / 2.0;
	
//	fprintf(stderr,"M = C1' * M\n");
//	fprintf(stderr,"%e %e %e\n",X2[0],X2[1],X2[2]);
//	fprintf(stderr,"%e %e %e\n",X2[3],X2[4],X2[5]);
//	fprintf(stderr,"%e %e %e\n",X2[6],X2[7],X2[8]);
	
	u32 result = gsl_eigen_nonsymmv(MI_g,EX_g,EV_g,W1_g);
	if ( result ) fprintf(stderr,"Error in fitting\n");
	
	X3 = gsl_matrix_ptr(TR_g,0,0);
	X4 = gsl_matrix_complex_ptr(EV_g,0,0);

	for(k=0;k<9;k++) EV_c[k] = GSL_REAL(X4[k]);
	for(k=0;k<9;k++) TR_c[k] = X3[k];

//	fprintf(stderr,"Eigenvectors\n");
//	fprintf(stderr,"%e %e %e\n",EV_c[0],EV_c[1],EV_c[2]);
//	fprintf(stderr,"%e %e %e\n",EV_c[3],EV_c[4],EV_c[5]);
//	fprintf(stderr,"%e %e %e\n",EV_c[6],EV_c[7],EV_c[8]);
	
//	fprintf(stderr,"Eigenvalues: ");
//	for(k=0;k<3;k++) fprintf(stderr,"%e ",GSL_REAL(gsl_vector_complex_get(EX_g,k)));
//	fprintf(stderr,"\n");
	
	for (k=0;k<3;k++) cond[k] = 4 * EV_c[k] * EV_c[k+6] - EV_c[k+3] * EV_c[k+3];
	
//	fprintf(stderr,"Conditional: ");
//	for(k=0;k<3;k++) {
//		if ( cond[k] < 0 ) fprintf(stderr,"0 ");
//		else fprintf(stderr,"1 ");
//	}
//	fprintf(stderr,"\n");
		
	for (k=0;k<3;k++) {
		if ( cond[k] > 0 ) {
			e[0] = EV_c[k];
			e[1] = EV_c[k+3];
			e[2] = EV_c[k+6];
			e[3] = e[0]*TR_c[0] + e[1]*TR_c[1] + e[2]*TR_c[2];
			e[4] = e[0]*TR_c[3] + e[1]*TR_c[4] + e[2]*TR_c[5];
			e[5] = e[0]*TR_c[6] + e[1]*TR_c[7] + e[2]*TR_c[8];
		}
	}

	if ( e[0] < 0 ) for (k=0;k<6;k++) e[k] = -e[k];
	
	f64 Ax = e[0];
	f64 Bx = e[1];
	f64 Cx = e[2];
	f64 Dx = e[3];
	f64 Ex = e[4];
	f64 Fx = e[5];
	
	return [Ellipse newWithA:Ax b:Bx c:Cx d:Dx e:Ex f:Fx];
	
}

-(id) free {
	[super free];
	return nil;
}

-(void) drawInArray:(ArrayP)array {

	u32 maxrow = [array sizeOfDimension: 1] - 1;
	u32 maxcol = [array sizeOfDimension: 0] - 1;
	f64 A1 = general[AX];
	f64 B1 = general[BX];
	f64 C1 = general[CX];
	f64 D1 = general[DX];
	f64 E1 = general[EX];
	f64 F1 = general[FX];
	
	u32 minr = 0;
	u32 maxr = maxrow;
	u32 minc = 0;
	u32 maxc = maxcol;

	minr = BOUND(0,minr,maxrow);
	maxr = BOUND(0,maxr,maxrow);
	minc = BOUND(0,minc,maxcol);
	maxc = BOUND(0,maxc,maxcol);
	
	f64 * image = [array data];
	
	u32 row, col;
	for(row=minr;row<=maxr;row++) {
		for(col=minc;col<=maxc;col++) {
			f64 x = col;
			f64 y = row;
			f64 vx = A1*x*x + B1*x*y + C1*y*y + D1*x + E1*y + F1;
			if ( vx <= 0.0 ) image[row*(maxcol+1)+col] *= 1.5;
	}}
	
}

-(void) toGeneralConic {
	
	f64 A = 1.0/(x_axis*x_axis);
	f64 C = 1.0/(y_axis*y_axis);
	f64 c = cos(rotation);
	f64 s = sin(rotation);

	/* These equations convert the standard ellipse parameters (given)

		(cos(phi)*(x-Xc))^2     (-sin(phi)*(y-Yc))^2
		-------------------  +  --------------------   = 0
		       Ma^2                     Mi^2

		to the general conic equation parameters

		A1*x*x + B1*x*y + C1*y*y + D1*x + E1*y + F = 0

	*/

	f64 A1 = A*c*c + C*s*s;
	f64 B1 = 2*c*s*(A-C);
	f64 C1 = A*s*s + C*c*c;
	f64 D1 = -2*A1*x_center - B1*y_center;
	f64 E1 = -2*C1*y_center - B1*x_center;
	f64 F1 = A1*x_center*x_center + B1*y_center*y_center + C1*y_center*y_center - 1;
	
	general[AX] = A1;
	general[BX] = B1;
	general[CX] = C1;
	general[DX] = D1;
	general[EX] = E1;
	general[FX] = F1;
	
}

-(void) toGeneralEllipse {
	
	// Ax, Bx, Cx, Dx, Ex, Fx are ellipse parameters in general conic form:
	// Ax*x^2 + Bx*x*y + Cx*y*y + Dx*x + Ex*y + Fx = 0
	
	f64 Ax = general[AX];
	f64 Bx = general[BX];
	f64 Cx = general[CX];
	f64 Dx = general[DX];
	f64 Ex = general[EX];
	f64 Fx = general[FX];
	
	// We can determine the ellipse rotation angle, u, using the general conic parameters A, B, and C and
	// the double angle identities sin(2u) = 2sin(u)cos(u) and cos(2u) = cos(u)^2 - sin(u)^2
	// so that tan(2u) = B / ( A - C ) = sin(2u)/cos(2u) and u = atan(2u)/2
	
	f64 phi = atan(Bx/(Cx-Ax))/2;
	
	f64 c = cos(phi);
	f64 s = sin(phi);
	
	// Once the angle is determined the other general ellipse parameters can be recovered
	// by reorienting the general conic parameters to an angle of 0, and determining the
	// other ellipse parmeters
	
	f64 Ad = Ax*c*c - Bx*c*s + Cx*s*s;
	f64 Cd = Ax*s*s + Bx*s*c + Cx*c*c;
	f64 Dd = Dx*c - Ex*s;
	f64 Ed = Dx*s + Ex*c;
	f64 Fd = (Dd*Dd)/(4.0*Ad) + (Ed*Ed)/(4.0*Cd) - Fx;
	
	f64 t1 = -Dd/(2*Ad);
	f64 t2 = -Ed/(2*Cd);
	
	f64 Xc = c*t1 + s*t2;
	f64 Yc = c*t2 - s*t1;
	f64 Mx = sqrt(Fd/Ad);
	f64 My = sqrt(Fd/Cd);
	
	rotation = phi;
	x_axis = Mx;
	y_axis = My;
	x_center = Xc;
	y_center = Yc;
	
}

-(void) findBounds {
	
	/* We now compute the ellipse limits (may be useful later) by finding
		the roots of two quadriatic equations based on the general conic equation
	*/

	f64 A = bounds[AX];
	f64 B = bounds[BX];
	f64 C = bounds[CX];
	f64 D = bounds[DX];
	f64 E = bounds[EX];
	f64 F = bounds[FX];
	
	f64 Qr, Rr;
	f64 Pr = 4*A*C - B*B;

	/* Top and Bottom (row) coordinates */
	Qr = 4*C*D - 2*E*B;
	Rr = 4*C*F - E*E;
	bounds[YHI] = (-Qr+sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);
	bounds[YLO] = (-Qr-sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);	

	/* Left and Right (col) coordinates */
	Qr = 4*A*E - 2*D*B;
	Rr = 4*A*F - D*D;
	bounds[XHI] = (-Qr+sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);
	bounds[XLO] = (-Qr-sqrt(Qr*Qr-4*Pr*Rr))/(2*Pr);
	
}

// Get and set general ellipse parameters

-(f64) x_axis {
	return x_axis;
}

-(f64) y_axis {
	return y_axis;
}

-(f64) major_axis {
	return MAX(x_axis,y_axis);
}

-(f64) minor_axis {
	return MIN(x_axis,y_axis);
}

-(f64) rotation {
	return rotation;
}

-(f64) majorRotation {
	if ( x_axis > y_axis ) {
		return rotation;
	} else {
		return rotation + PI/2.0;
	}
}

-(f64) minorRotation {
	if ( x_axis < y_axis ) {
		return rotation;
	} else {
		return rotation + PI/2.0;
	}
}

-(f64) x_center {
	return x_center;
}

-(f64) y_center {
	return y_center;
}

-(void) setX_axis:(f64)newx {
	x_axis = newx;
	[self toGeneralConic];
	[self findBounds];
}

-(void) setY_axis:(f64)newy {
	y_axis = newy;
	[self toGeneralConic];
	[self findBounds];
}

-(void) setX_center:(f64)newx {
	x_center = newx;
	[self toGeneralConic];
	[self findBounds];
}

-(void) setY_center:(f64)newy {
	y_center = newy;
	[self toGeneralConic];
	[self findBounds];
}

-(void) setRotation:(f64)newr {
	rotation = newr;
	[self toGeneralConic];
	[self findBounds];
}

-(void) setX_axis:(f64)xa y_axis:(f64)ya x_center:(f64)xc y_center:(f64)yc rotation:(f64)r {
	x_axis = xa;
	y_axis = ya;
	x_center = xc;
	y_center = yc;
	rotation = r;
	[self toGeneralConic];
	[self findBounds];
}

// Get and set general conic parameters

-(f64) A {
	return general[AX];
}

-(f64) B {
	return general[BX];
}

-(f64) C {
	return general[CX];
}

-(f64) D {
	return general[DX];
}

-(f64) E {
	return general[EX];
}

-(f64) F {
	return general[FX];
}

-(f64 *) general {
	f64 * gn = NEWV(f64,6);
	memcpy(gn,general,sizeof(f64)*6);
	return gn;
} 

-(void) setA:(f64)A {
	general[AX] = A;
	[self toGeneralEllipse];
	[self findBounds];
}

-(void) setB:(f64)B {
	general[BX] = B;
	[self toGeneralEllipse];
	[self findBounds];
}

-(void) setC:(f64)C {
	general[CX] = C;
	[self toGeneralEllipse];
	[self findBounds];
}

-(void) setD:(f64)D {
	general[DX] = D;
	[self toGeneralEllipse];
	[self findBounds];
}

-(void) setE:(f64)E {
	general[EX] = E;
	[self toGeneralEllipse];
	[self findBounds];
}

-(void) setF:(f64)F {
	general[FX] = F;
	[self toGeneralEllipse];
	[self findBounds];
}

-(void) setGeneralA:(f64)A B:(f64)B C:(f64)C D:(f64)D E:(f64)E F:(f64)F {
	general[AX] = A;
	general[BX] = B;
	general[CX] = C;
	general[DX] = D;
	general[EX] = E;
	general[FX] = F;
	[self toGeneralEllipse];
	[self findBounds];
}

-(void) printInfoTo:(FILE *)fp {
	fprintf(fp,"A: %e B: %e C: %e D: %e E: %e F: %e\n",general[AX],general[BX],general[CX],general[DX],general[EX],general[FX]);
	fprintf(fp,"Xc: %e Yc: %e Ax: %e Ay: %e phi: %2.2f\n",x_center,y_center,x_axis,y_axis,rotation*DEG);
	fprintf(fp,"Axis ratio: %e\n",MAX(x_axis,y_axis)/MIN(x_axis,y_axis));
}

-(u08) isValid {
	
//	if ( !ISFINITE(general[AX]) ) return FALSE;
//	if ( !ISFINITE(general[BX]) ) return FALSE;
//	if ( !ISFINITE(general[CX]) ) return FALSE;
//	if ( !ISFINITE(general[DX]) ) return FALSE;
//	if ( !ISFINITE(general[EX]) ) return FALSE;
//	if ( !ISFINITE(general[FX]) ) return FALSE;
	
	if ( !ISFINITE(x_axis) ) return FALSE;
	if ( !ISFINITE(y_axis) ) return FALSE;
	if ( !ISFINITE(x_center) ) return FALSE;
	if ( !ISFINITE(y_center) ) return FALSE;
	if ( !ISFINITE(rotation) ) return FALSE;
	
	return TRUE;
	
}

@end
