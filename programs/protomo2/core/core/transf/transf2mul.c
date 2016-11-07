/*----------------------------------------------------------------------------*
*
*  transf2mul.c  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transf2.h"


/* functions */

extern Status Transf2Mul
              (Coord A[3][2],
               Coord B[3][2],
               Coord C[3][2])

{
  Coord c00  =  A[0][0] * B[0][0]  +  A[0][1] * B[1][0];
  Coord c01  =  A[0][0] * B[0][1]  +  A[0][1] * B[1][1];

  Coord c10  =  A[1][0] * B[0][0]  +  A[1][1] * B[1][0];
  Coord c11  =  A[1][0] * B[0][1]  +  A[1][1] * B[1][1];

  Coord c20  =  A[2][0] * B[0][0]  +  A[2][1] * B[1][0]  +  B[2][0];
  Coord c21  =  A[2][0] * B[0][1]  +  A[2][1] * B[1][1]  +  B[2][1];

  C[0][0] = c00;  C[0][1] = c01;
  C[1][0] = c10;  C[1][1] = c11;
  C[2][0] = c20;  C[2][1] = c21;

  return E_NONE;

}
