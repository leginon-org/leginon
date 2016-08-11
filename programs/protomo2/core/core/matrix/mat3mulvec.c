/*----------------------------------------------------------------------------*
*
*  mat3mulvec.c  -  3 x 3 matrix operations
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

extern Status Mat3MulVec
              (Coord A[3][3],
               Coord B[3],
               Coord C[3])

{
  Coord c0  =  A[0][0] * B[0]  +  A[0][1] * B[1]  +  A[0][2] * B[2];
  Coord c1  =  A[1][0] * B[0]  +  A[1][1] * B[1]  +  A[1][2] * B[2];
  Coord c2  =  A[2][0] * B[0]  +  A[2][1] * B[1]  +  A[2][2] * B[2];

  C[0] = c0;  C[1] = c1;  C[2] = c2;

  return E_NONE;

}
