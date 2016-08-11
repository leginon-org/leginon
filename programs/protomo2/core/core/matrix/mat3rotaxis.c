/*----------------------------------------------------------------------------*
*
*  mat3rotaxis.c  -  3 x 3 matrix operations
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

extern Status Mat3RotAxis
              (const Coord a[3],
               Coord phi,
               Coord A[3][3])

{
  Coord wx  = a[0], wy=a[1], wz=a[2];
  Coord wx2 = wx * wx, wy2 = wy * wy, wz2 = wz * wz;
  Coord w2  = wx2 + wy2 + wz2;
  Coord w   = sqrt(w2);

  if (w > 0) {

    Coord sinphi = sin(phi) / w;
    Coord cosphi = ( 1 - cos(phi) ) / w2;

    A[0][0] = 1 - (wy2+wz2) * cosphi;
    A[0][1] =  wz * sinphi  +  wx * wy * cosphi;
    A[0][2] = -wy * sinphi  +  wx * wz * cosphi;

    A[1][0] = -wz * sinphi  +  wx * wy * cosphi;
    A[1][1] = 1 - (wx2 + wz2) * cosphi;
    A[1][2] =  wx * sinphi  +  wy * wz * cosphi;

    A[2][0] =  wy * sinphi  +  wx * wz * cosphi;
    A[2][1] = -wx * sinphi  +  wy * wz * cosphi;
    A[2][2] = 1 - (wx2 + wy2) * cosphi;

  } else {

    A[0][0] = 1; A[0][1] = 0; A[0][2] = 0;
    A[1][0] = 0; A[1][1] = 1; A[1][2] = 0;
    A[2][0] = 0; A[2][1] = 0; A[2][2] = 1;

  }

  return E_NONE;

}
