/*----------------------------------------------------------------------------*
*
*  mat3rotdir.c  -  3 x 3 matrix operations
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

extern Status Mat3RotDir
              (const Coord dir[3],
               const Coord phi,
               Coord A[3][3])

{
  Coord r   = sqrt( dir[0] * dir[0]  +  dir[1] * dir[1]  +  dir[2] * dir[2] );
  Coord rxy = sqrt( dir[0] * dir[0]  +  dir[1] * dir[1] );
  Coord cosphi = cos(phi), sinphi = sin(phi);

  if ((r > 0) && (rxy > 0)) {

    Coord costheta =  dir[2] / r,   sintheta = rxy / r;
    Coord cospsi   = -dir[1] / rxy, sinpsi   = dir[0] / rxy;

    Coord a00 = 1 - sinpsi * sinpsi * (1 - costheta);
    Coord a01 =     cospsi * sinpsi * (1 - costheta);
    Coord a02 =    -sinpsi * sintheta;
    Coord a10 =     cospsi * sinpsi * ( 1 - costheta);
    Coord a11 = 1 - cospsi * cospsi * ( 1 - costheta);
    Coord a12 =     cospsi * sintheta;

    A[0][0] =  a00 * cosphi  +  a10 * sinphi;
    A[0][1] =  a01 * cosphi  +  a11 * sinphi;
    A[0][2] =  a02 * cosphi  +  a12 * sinphi;

    A[1][0] = -a00 * sinphi+a10 * cosphi;
    A[1][1] = -a01 * sinphi+a11 * cosphi;
    A[1][2] = -a02 * sinphi+a12 * cosphi;

    A[2][0] =  sinpsi * sintheta;
    A[2][1] = -cospsi * sintheta;
    A[2][2] =  costheta;

  } else {

    A[0][0] = cosphi;
    A[0][1] = sinphi;
    A[0][2] = 0;
    A[1][0] = -sinphi;
    A[1][1] = cosphi;
    A[1][2] = 0;
    A[2][0] = 0;
    A[2][1] = 0;
    A[2][2] = 1;

  }

  return E_NONE;

}
