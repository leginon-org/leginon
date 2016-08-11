/*----------------------------------------------------------------------------*
*
*  mat3.h  -  core: matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef mat3_h_
#define mat3_h_

#include "matdefs.h"


/* prototypes */

extern Status Mat3Unit
              (Coord A[3][3]);

extern Status Mat3Diag
              (const Coord A[3],
               Coord B[3][3]);

extern Status Mat3Transp
              (Coord A[3][3],
               Coord B[3][3]);

extern Status Mat3Inv
              (Coord A[3][3],
               Coord B[3][3],
               Coord *det);

extern Status Mat3Rot
              (const Coord eul[3],
               Coord A[3][3]);

extern Status Mat3RotInv
              (const Coord eul[3],
               Coord A[3][3]);

extern Status Mat3Euler
              (Coord A[3][3],
               Coord eul[3]);

extern Status Mat3RotAxis
              (const Coord a[3],
               Coord phi,
               Coord A[3][3]);

extern Status Mat3RotDir
              (const Coord dir[3],
               const Coord phi,
               Coord A[3][3]);

extern Status Mat3RotX
              (const Coord phi,
               Coord A[3][3]);

extern Status Mat3RotY
              (const Coord  phi,
               Coord A[3][3]);

extern Status Mat3RotZ
              (const Coord phi,
               Coord A[3][3]);

extern Status Mat3Mul
              (Coord A[3][3],
               Coord B[3][3],
               Coord C[3][3]);

extern Status Mat3MulTransp
              (Coord A[3][3],
               Coord B[3][3],
               Coord C[3][3]);

extern Status Mat3TranspMul
              (Coord A[3][3],
               Coord B[3][3],
               Coord C[3][3]);

extern Status Mat3MulVec
              (Coord A[3][3],
               Coord B[3],
               Coord C[3]);

extern Status Mat3TranspMulVec
              (Coord A[3][3],
               Coord B[3],
               Coord C[3]);

extern Status Mat3VecMul
              (Coord A[3],
               Coord B[3][3],
               Coord C[3]);

extern Status Mat3Svd
              (Coord A[3][3],
               Coord U[3][3],
               Coord S[3],
               Coord V[3][3]);


#endif
