/*----------------------------------------------------------------------------*
*
*  mat2transp.c  -  2 x 2 matrix operations
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

extern Status Mat2Transp
              (Coord A[2][2],
               Coord B[2][2])
{
  Coord b00 = A[0][0], b01 = A[1][0];
  Coord b10 = A[0][1], b11 = A[1][1];

  B[0][0] = b00; B[0][1] = b01;
  B[1][0] = b10; B[1][1] = b11;

  return E_NONE;

}
