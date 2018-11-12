/*----------------------------------------------------------------------------*
*
*  mat3roty.c  -  3 x 3 matrix operations
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
#include "mathdefs.h"


/* functions */

extern Status Mat3RotY
              (const Coord  phi,
               Coord A[3][3])

{
  Coord cosphi = cos(phi);
  Coord sinphi = sin(phi);

  A[0][0] = cosphi;  A[0][1] = 0;  A[0][2] = -sinphi;
  A[1][0] = 0;       A[1][1] = 1;  A[1][2] =  0;
  A[2][0] = sinphi;  A[2][1] = 0;  A[2][2] =  cosphi;

  return E_NONE;

}
