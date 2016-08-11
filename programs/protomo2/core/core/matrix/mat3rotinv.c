/*----------------------------------------------------------------------------*
*
*  mat3rotinv.c  -  3 x 3 matrix operations
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

extern Status Mat3RotInv
              (const Coord eul[3],
               Coord A[3][3])

{
  Coord cospsi   = cos(eul[0]), sinpsi   = sin(eul[0]);
  Coord costheta = cos(eul[1]), sintheta = sin(eul[1]);
  Coord cosphi   = cos(eul[2]), sinphi   = sin(eul[2]);

  A[0][0] =  cospsi * cosphi  -  sinpsi * costheta * sinphi;
  A[1][0] =  sinpsi * cosphi  +  cospsi * costheta * sinphi;
  A[2][0] =                               sintheta * sinphi;
  A[0][1] = -cospsi * sinphi  -  sinpsi * costheta * cosphi;
  A[1][1] = -sinpsi * sinphi  +  cospsi * costheta * cosphi;
  A[2][1] =                               sintheta * cosphi;
  A[0][2] =  sinpsi * sintheta;
  A[1][2] = -cospsi * sintheta;
  A[2][2] =           costheta;

  return E_NONE;

}
