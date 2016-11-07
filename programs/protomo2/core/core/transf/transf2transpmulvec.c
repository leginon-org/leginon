/*----------------------------------------------------------------------------*
*
*  transf2transpmulvec.c  -  core: linear transformations
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

extern Status Transf2TranspMulVec
              (Coord A[3][2],
               Coord B[2],
               Coord C[2])

{
  Coord c0 = A[0][0] * B[0] + A[1][0] * B[1] + A[2][0];
  Coord c1 = A[0][1] * B[0] + A[1][1] * B[1] + A[2][1];

  C[0] = c0; C[1] = c1;

  return E_NONE;
}
