/*----------------------------------------------------------------------------*
*
*  mat2rot.c  -  2 x 2 matrix operations
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
#include "mathdefs.h"


/* functions */

extern Status Mat2Rot
              (const Coord *rot,
               Coord A[2][2])

{
  Coord phi = *rot;

  A[0][0] = cos(phi);  A[0][1] = sin(phi);
  A[1][0] = -A[0][1];  A[1][1] = A[0][0];

  return E_NONE;

}
