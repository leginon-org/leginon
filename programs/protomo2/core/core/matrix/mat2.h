/*----------------------------------------------------------------------------*
*
*  mat2.h  -  core: matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef mat2_h_
#define mat2_h_

#include "matdefs.h"



/* prototypes */

extern Status Mat2Unit
              (Coord A[2][2]);

extern Status Mat2Diag
              (const Coord A[2],
               Coord B[2][2]);

extern Status Mat2Transp
              (Coord A[2][2],
               Coord B[2][2]);

extern Status Mat2Inv
              (Coord A[2][2],
               Coord B[2][2],
               Coord *det);

extern Status Mat2Rot
              (const Coord *rot,
               Coord A[2][2]);

extern Status Mat2RotInv
              (const Coord *rot,
               Coord A[2][2]);

extern Status Mat2Mul
              (Coord A[2][2],
               Coord B[2][2],
               Coord C[2][2]);

extern Status Mat2MulTransp
              (Coord A[2][2],
               Coord B[2][2],
               Coord C[2][2]);

extern Status Mat2TranspMul
              (Coord A[2][2],
               Coord B[2][2],
               Coord C[2][2]);

extern Status Mat2MulVec
              (Coord A[2][2],
               Coord B[2],
               Coord C[2]);

extern Status Mat2TranspMulVec
              (Coord A[2][2],
               Coord B[2],
               Coord C[2]);

extern Status Mat2VecMul
              (Coord A[2],
               Coord B[2][2],
               Coord C[2]);

extern Status Mat2Svd
              (Coord A[2][2],
               Coord U[2][2],
               Coord S[2],
               Coord V[2][2]);


#endif
