#ifndef libCV_ellipse
#define libCV_ellipse

#include <objc/Object.h>
#include "cvtypes.h"
#include "util.h"
#include "Array.h"
#include <gsl/gsl_math.h>
#include <gsl/gsl_linalg.h>
#include <gsl/gsl_blas.h>
#include <gsl/gsl_eigen.h>

@interface Ellipse : Object {
	
	f64 x_axis;
	f64 y_axis;
	f64 x_center;
	f64 y_center;
	f64 rotation;
	
	f64 general[6];
	
	f64 bounds[4];
	
}

+(id) newAtX:(f64)xc andY:(f64)yc withXAxis:(f64)xa andYAxis:(f64)ya rotatedBy:(f64)phi;
+(id) newWithA:(f64)a b:(f64)b c:(f64)c d:(f64)d e:(f64)e f:(f64)f;

+(id) newFromPoints:(ArrayP)points;

-(void) drawInArray:(ArrayP)array;

-(void) toGeneralConic;
-(void) toGeneralEllipse;
-(void) findBounds;

// Get and set general ellipse parameters

-(f64) x_axis;
-(f64) y_axis;
-(f64) major_axis;
-(f64) minor_axis;
-(f64) rotation;
-(f64) majorRotation;
-(f64) minorRotation;
-(f64) x_center;
-(f64) y_center;

-(void) setX_axis:(f64)newx;
-(void) setY_axis:(f64)newy;
-(void) setX_center:(f64)newx;
-(void) setY_center:(f64)newy;
-(void) setRotation:(f64)newr;
-(void) setX_axis:(f64)xa y_axis:(f64)ya x_center:(f64)xc y_center:(f64)yc rotation:(f64)r;

// Get and set general conic parameters

-(f64) A;
-(f64) B;
-(f64) C;
-(f64) D;
-(f64) E;
-(f64) F;

-(f64 *) general;

-(void) setA:(f64)A;
-(void) setB:(f64)B;
-(void) setC:(f64)C;
-(void) setD:(f64)D;
-(void) setE:(f64)E;
-(void) setF:(f64)F;
-(void) setGeneralA:(f64)A B:(f64)B C:(f64)C D:(f64)D E:(f64)E F:(f64)F;

-(void) printInfoTo:(FILE *)fp;

-(u08) isValid;
-(id) release;

@end

enum ellipseindices {
	AX,
	BX,
	CX,
	DX,
	EX,
	FX,
};

enum ellipsebounds {
	XHI,
	XLO,
	YHI,
	YLO,
};

typedef Ellipse * EllipseP;

#endif
