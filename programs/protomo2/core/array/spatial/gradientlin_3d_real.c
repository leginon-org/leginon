/*----------------------------------------------------------------------------*
*
*  gradientlin_3d_real.c  -  array: spatial operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "spatial.h"
#include "exception.h"


/* functions */

extern Status GradientLin3dReal
              (const Size *srclen,
               const void *srcaddr,
               Coord *c)

{

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( c == NULL ) ) return exception( E_ARGVAL );

  Size nx = srclen[0];
  Size ny = srclen[1];
  Size nz = srclen[2];

  c[0] = 0;
  c[1] = 0;
  c[2] = 0;
  c[3] = 0;

  Coord n = nx * ny * nz;
  if ( n == 0 ) return E_NONE;

  Coord s0 = 0;
  Coord sx = 0;
  Coord sy = 0;
  Coord sz = 0;

  const Real *src = srcaddr;
  Coord u = 0;
  for ( Size iz = 0; iz < nz; iz++ ) {
    Coord t = 0;
    for ( Size iy = 0; iy < ny; iy++ ) {
      Coord s = 0;
      for ( Size ix = 0; ix < nx; ix++ ) {
        s += *src++;
      }
      t += s;
    }
    u += t;
  }
  c[0] = u / n;

  src = srcaddr;
  for ( Size iz = 0; iz < nz; iz++ ) {
    Coord t0 = 0,tx = 0,ty = 0;
    for ( Size iy = 0; iy < ny; iy++ ) {
      Coord u0 = 0,ux = 0;
      for ( Size ix = 0; ix < nx; ix++ ) {
        Coord s = *src++; s -= c[0];
        u0 += s;
        ux += s * ix;
      }
      t0 += u0;
      tx += ux;
      ty += u0 * iy;
    }
    s0 += t0;
    sx += tx;
    sy += ty;
    sz += t0 * iz;
  }

  c[0] -= 6 * ( sx / ( nx + 1 ) + sy / ( ny + 1 ) + sz / ( nz + 1 ) ) / n;
  if ( nx > 1 ) {
    c[1] = 6 * ( 2 * sx / ( nx - 1 ) - s0 ) / ( nx + 1 ) / n;
  }
  if ( ny > 1 ) {
    c[2] = 6 * ( 2 * sy / ( ny - 1 ) - s0 ) / ( ny + 1 ) / n;
  }
  if ( nz > 1 ) {
    c[3] = 6 * ( 2 * sz / ( nz - 1 ) - s0 ) / ( nz + 1 ) / n;
  }

  return E_NONE;

}
