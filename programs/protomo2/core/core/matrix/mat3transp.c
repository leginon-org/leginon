/*----------------------------------------------------------------------------*
*
*  mat3transp.c  -  3 x 3 matrix operations
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

extern Status Mat3Transp
              (Coord A[3][3],
               Coord B[3][3])
{
  Coord b00 = A[0][0], b01 = A[1][0], b02 = A[2][0];
  Coord b10 = A[0][1], b11 = A[1][1], b12 = A[2][1];
  Coord b20 = A[0][2], b21 = A[1][2], b22 = A[2][2];

  B[0][0] = b00; B[0][1] = b01; B[0][2] = b02;
  B[1][0] = b10; B[1][1] = b11; B[1][2] = b12;
  B[2][0] = b20; B[2][1] = b21; B[2][2] = b22;

  return E_NONE;

}
