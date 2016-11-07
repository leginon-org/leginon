/*----------------------------------------------------------------------------*
*
*  maskcommon.h  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef maskcommon_h_
#define maskcommon_h_

#include "mask.h"


/* macros */

#define MaskMulVec2( A, b, c )                       \
  {                                                  \
    c[0] = A[0] * b[0] + A[1] * b[1];                \
    c[1] = A[2] * b[0] + A[3] * b[1];                \
  }


#define MaskMulVec3( A, b, c )                       \
  {                                                  \
    c[0] = A[0] * b[0] + A[1] * b[1] + A[2] * b[2];  \
    c[1] = A[3] * b[0] + A[4] * b[1] + A[5] * b[2];  \
    c[2] = A[6] * b[0] + A[7] * b[1] + A[8] * b[2];  \
  }


#define MASK_ERFLIMIT 5.92155

#define MaskErf( x )  ( ( ( x < -MASK_ERFLIMIT ) || ( x > MASK_ERFLIMIT ) ) ? 0 : Erf( x ) )

#define MaskErfEval( f, q, t )                \
  {                                           \
    Coord  x1 = ( q + 1 ) / t;                \
    Coord  x2 = ( q - 1 ) / t;                \
    if ( x1 < -MASK_ERFLIMIT ) {              \
      f = 0;                                  \
    } else if ( x2 < -MASK_ERFLIMIT ) {       \
      if ( x1 < MASK_ERFLIMIT ) {             \
        f = 0.5 * ( Erf( x1 ) + 1 );          \
      } else {                                \
        f = 1;                                \
      }                                       \
    } else if ( x2 < MASK_ERFLIMIT ) {        \
      if ( x1 < MASK_ERFLIMIT ) {             \
        f = 0.5 * ( Erf( x1 ) - Erf( x2 ) );  \
      } else {                                \
        f = 0.5 * ( 1 - Erf( x2 ) );          \
      }                                       \
    } else {                                  \
      f = 0;                                  \
    }                                         \
  }


/* prototypes */

extern void MaskSetupParam
            (Size dim,
             const Size *len,
             const Coord *b,
             const Coord *w,
             Coord *c,
             Coord *p,
             MaskFlags flags);

extern void MaskSetupParamApod
            (Size dim,
             const Size *len,
             const Coord *b,
             const Coord *w,
             const Coord *s,
             Coord *c,
             Coord *p,
             Coord *t,
             MaskFlags flags);

extern void MaskSetupMat
            (Size dim,
             const Coord *A,
             const Coord *p,
             Coord *B);


#endif
