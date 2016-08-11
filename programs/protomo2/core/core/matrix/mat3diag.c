/*----------------------------------------------------------------------------*
*
*  mat3diag.c  -  3 x 3 matrix operations
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

extern Status Mat3Diag
              (const Coord A[3],
               Coord B[3][3])

{

  B[0][0] = A[0]; B[0][1] =0;    B[0][2] = 0;
  B[1][0] = 0;    B[1][1] =A[1]; B[1][2] = 0;
  B[2][0] = 0;    B[2][1] =0;    B[2][2] = A[2];

  return E_NONE;

}
