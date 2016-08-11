/*----------------------------------------------------------------------------*
*
*  mat2transpmul.c  -  2 x 2 matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mat2.h"


/* functions */

extern Status Mat2TranspMul
              (Coord A[2][2],
               Coord B[2][2],
               Coord C[2][2])

{
  Coord c00 = A[0][0] * B[0][0] + A[1][0] * B[1][0];
  Coord c01 = A[0][0] * B[0][1] + A[1][0] * B[1][1];
  Coord c10 = A[0][1] * B[0][0] + A[1][1] * B[1][0];
  Coord c11 = A[0][1] * B[0][1] + A[1][1] * B[1][1];

  C[0][0] = c00; C[0][1] = c01;
  C[1][0] = c10; C[1][1] = c11;

  return E_NONE;
}
