/*----------------------------------------------------------------------------*
*
*  mathdefs.h  -  mathematical constants and functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef mathdefs_h_
#define mathdefs_h_

#include <math.h>


/* typed math functions for coordinates etc. */

#define Pi	       3.14159265358979323846
#define Pi2	       1.57079632679489661923
#define Fabs(x)        fabs(x)
#define Sqrt(x)        sqrt(x)
#define Hypot(x,y)     hypot(x,y)
#define Exp(x)         exp(x)
#define Pow(x,y)       pow(x,y)
#define Log(x)         log(x)
#define Log10(x)       log10(x)
#define Erf(x)         erf(x)
#define Cos(x)         cos(x)
#define Sin(x)         sin(x)
#define Tan(x)         tan(x)
#define Acos(x)        acos(x)
#define Asin(x)        asin(x)
#define Atan(x)        atan(x)
#define Atan2(y,x)     atan2(y,x)
#define Ceil(x)        ceil(x)
#define Floor(x)       floor(x)
#define Rint(x)        rint(x)
#define Round(x)       round(x)
#define Trunc(x)       trunc(x)
#define Fmod(x,y)      fmod(x,y)
#define Copysign(x,y)  copysign(x,y)

#ifdef COMPLEX

#define Creal(x)       creal(x)
#define Cimag(x)       cimag(x)
#define Cassign(z,x,y) ((z)=((Coord)(x))+(ImagI*((Coord)(y))))

#else

#define Creal(x)       ((x).array[0])
#define Cimag(x)       ((x).array[1])
#define Cassign(z,x,y) ((z).array[0]=((Coord)(x)),(z).array[1]=((Coord)(y)))

#endif


/* typed math functions for image data */

#if REALBITS == 32

#define CnPi             3.14159265358979323846f
#define CnPi2            1.57079632679489661923f
#define FnFabs(x)        fabsf(x)
#define FnSqrt(x)        sqrtf(x)
#define FnHypot(x,y)     hypotf(x,y)
#define FnExp(x)         expf(x)
#define FnPow(x,y)       powf(x,y)
#define FnLog(x)         logf(x)
#define FnLog10(x)       log10f(x)
#define FnErf(x)         erff(x)
#define FnCos(x)         cosf(x)
#define FnSin(x)         sinf(x)
#define FnTan(x)         tanf(x)
#define FnAcos(x)        acosf(x)
#define FnAsin(x)        asinf(x)
#define FnAtan(x)        atanf(x)
#define FnAtan2(y,x)     atan2f(y,x)
#define FnCeil(x)        ceilf(x)
#define FnFloor(x)       floorf(x)
#define FnRint(x)        rintf(x)
#define FnRound(x)       roundf(x)
#define FnTrunc(x)       truncf(x)
#define FnFmod(x,y)      fmodf(x,y)
#define FnCopysign(x,y)  copysignf(x,y)

#ifdef COMPLEX

#define Re(x)            crealf(x)
#define Im(x)            cimagf(x)
#define Cset(z,x,y)      ((z)=((Real32)(x))+(ImagI*((Real32)(y))))

#else

#define Re(x)            ((x).array[0])
#define Im(x)            ((x).array[1])
#define Cset(z,x,y)      ((z).array[0]=(x),(z).array[1]=(y))

#endif

#elif REALBITS == 64

#define CnPi             3.14159265358979323846
#define CnPi2            1.57079632679489661923
#define FnFabs(x)        fabs(x)
#define FnSqrt(x)        sqrt(x)
#define FnHypot(x,y)     hypot(x,y)
#define FnExp(x)         exp(x)
#define FnPow(x,y)       pow(x,y)
#define FnLog(x)         log(x)
#define FnLog10(x)       log10(x)
#define FnErf(x)         erf(x)
#define FnCos(x)         cos(x)
#define FnSin(x)         sin(x)
#define FnTan(x)         tan(x)
#define FnAcos(x)        acos(x)
#define FnAsin(x)        asin(x)
#define FnAtan(x)        atan(x)
#define FnAtan2(y,x)     atan2(y,x)
#define FnCeil(x)        ceil(x)
#define FnFloor(x)       floor(x)
#define FnRint(x)        rint(x)
#define FnRound(x)       round(x)
#define FnTrunc(x)       trunc(x)
#define FnFmod(x,y)      fmod(x,y)
#define FnCopysign(x,y)  copysign(x,y)

#ifdef COMPLEX

#define Re(x)            creal(x)
#define Im(x)            cimag(x)
#define Cset(z,x,y)      ((z)=((Real64)(x))+(ImagI*((Real64)(y))))

#else

#define Re(x)            ((x).array[0])
#define Im(x)            ((x).array[1])
#define Cset(z,x,y)      ((z).array[0]=(x),(z).array[1]=(y))

#endif

#endif


/* temporary */

#undef M_PI
#undef M_PI_2
#undef M_PI_4
#undef M_1_PI
#undef M_2_PI
#undef M_2_SQRTPI


#endif
