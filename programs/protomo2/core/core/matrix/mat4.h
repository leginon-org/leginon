/*----------------------------------------------------------------------------*
*
*  mat4.h  -  core: matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef mat4_h_
#define mat4_h_

#include "matdefs.h"


/* prototypes */

extern Status Mat4Unit
              (Coord A[4][4]);

extern Status Mat4Diag
              (const Coord A[4],
               Coord B[4][4]);

extern Status Mat4Transp
              (Coord A[4][4],
               Coord B[4][4]);

extern Status Mat4Inv
              (Coord A[4][4],
               Coord B[4][4],
               Coord *det);

extern Status Mat4Mul
              (Coord A[4][4],
               Coord B[4][4],
               Coord C[4][4]);

extern Status Mat4MulTransp
              (Coord A[4][4],
               Coord B[4][4],
               Coord C[4][4]);

extern Status Mat4TranspMul
              (Coord A[4][4],
               Coord B[4][4],
               Coord C[4][4]);

extern Status Mat4MulVec
              (Coord A[4][4],
               Coord B[4],
               Coord C[4]);

extern Status Mat4TranspMulVec
              (Coord A[4][4],
               Coord B[4],
               Coord C[4]);

extern Status Mat4VecMul
              (Coord A[4],
               Coord B[4][4],
               Coord C[4]);

extern Status Mat4Svd
              (Coord A[4][4],
               Coord U[4][4],
               Coord S[4],
               Coord V[4][4]);


#endif
