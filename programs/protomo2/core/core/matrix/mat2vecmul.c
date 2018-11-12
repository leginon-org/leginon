/*----------------------------------------------------------------------------*
*
*  mat2vecmul.c  -  2 x 2 matrix operations
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

extern Status Mat2VecMul
              (Coord A[2],
               Coord B[2][2],
               Coord C[2])

{
  Coord c0 = A[0] * B[0][0] + A[1] * B[1][0];
  Coord c1 = A[0] * B[0][1] + A[1] * B[1][1];

  C[0] = c0; C[1] = c1;

  return E_NONE;
}
