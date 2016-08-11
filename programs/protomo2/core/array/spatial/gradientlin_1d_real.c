/*----------------------------------------------------------------------------*
*
*  gradientlin_1d_real.c  -  array: spatial operations
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

extern Status GradientLin1dReal
              (const Size *srclen,
               const void *srcaddr,
               Coord *c)

{

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( c == NULL ) ) return exception( E_ARGVAL );

  Size nx = srclen[0];

  Coord s0 = 0;
  Coord sx = 0;

  c[0] = 0;
  c[1] = 0;

  Coord n = nx;
  if ( n == 0 ) return E_NONE;

  const Real *src = srcaddr;
  Coord s = 0;
  for ( Size ix = 0; ix < nx; ix++ ) {
    s += *src++;
  }
  c[0] = s / n;

  src = srcaddr;
  for ( Size ix = 0; ix < nx; ix++ ) {
    Coord s = *src++; s -= c[0];
    s0 += s;
    sx += s * ix;
  }

  c[0] -= 6 * ( sx / ( nx + 1 ) ) / n;
  if ( nx > 1 ) {
    c[1] = 6 * ( 2 * sx / ( nx - 1 ) - s0 ) / ( nx + 1 ) / n;
  }

  return E_NONE;

}
