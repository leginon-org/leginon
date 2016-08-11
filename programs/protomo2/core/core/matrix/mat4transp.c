/*----------------------------------------------------------------------------*
*
*  mat4transp.c  -  4 x 4 matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mat4.h"


/* functions */

extern Status Mat4Transp
              (Coord A[4][4],
               Coord B[4][4])
{
  Coord b00 = A[0][0], b01 = A[1][0], b02 = A[2][0], b03 = A[3][0];
  Coord b10 = A[0][1], b11 = A[1][1], b12 = A[2][1], b13 = A[3][1];
  Coord b20 = A[0][2], b21 = A[1][2], b22 = A[2][2], b23 = A[3][2];
  Coord b30 = A[0][3], b31 = A[1][3], b32 = A[2][3], b33 = A[3][3];

  B[0][0] = b00; B[0][1] = b01; B[0][2] = b02; B[0][3] = b03;
  B[1][0] = b10; B[1][1] = b11; B[1][2] = b12; B[1][3] = b13;
  B[2][0] = b20; B[2][1] = b21; B[2][2] = b22; B[2][3] = b23;
  B[3][0] = b30; B[3][1] = b31; B[3][2] = b32; B[3][3] = b33;

  return E_NONE;

}
