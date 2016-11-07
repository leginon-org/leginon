/*----------------------------------------------------------------------------*
*
*  mat3mul.c  -  3 x 3 matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mat3.h"


/* functions */

extern Status Mat3Mul
              (Coord A[3][3],
               Coord B[3][3],
               Coord C[3][3])
{
  Coord c00  =  A[0][0] * B[0][0]  +  A[0][1] * B[1][0]  +  A[0][2] * B[2][0];
  Coord c01  =  A[0][0] * B[0][1]  +  A[0][1] * B[1][1]  +  A[0][2] * B[2][1];
  Coord c02  =  A[0][0] * B[0][2]  +  A[0][1] * B[1][2]  +  A[0][2] * B[2][2];

  Coord c10  =  A[1][0] * B[0][0]  +  A[1][1] * B[1][0]  +  A[1][2] * B[2][0];
  Coord c11  =  A[1][0] * B[0][1]  +  A[1][1] * B[1][1]  +  A[1][2] * B[2][1];
  Coord c12  =  A[1][0] * B[0][2]  +  A[1][1] * B[1][2]  +  A[1][2] * B[2][2];

  Coord c20  =  A[2][0] * B[0][0]  +  A[2][1] * B[1][0]  +  A[2][2] * B[2][0];
  Coord c21  =  A[2][0] * B[0][1]  +  A[2][1] * B[1][1]  +  A[2][2] * B[2][1];
  Coord c22  =  A[2][0] * B[0][2]  +  A[2][1] * B[1][2]  +  A[2][2] * B[2][2];

  C[0][0] = c00;  C[0][1] = c01;  C[0][2] = c02;
  C[1][0] = c10;  C[1][1] = c11;  C[1][2] = c12;
  C[2][0] = c20;  C[2][1] = c21;  C[2][2] = c22;

  return E_NONE;

}
