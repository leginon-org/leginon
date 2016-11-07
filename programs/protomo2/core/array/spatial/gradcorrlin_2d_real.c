/*----------------------------------------------------------------------------*
*
*  gradcorrlin_2d_real.c  -  array: spatial operations
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

extern Status GradcorrLin2dReal
              (const Size *dstlen,
               void *dstaddr,
               const Coord *c)

{
  if ( argcheck( dstlen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( c == NULL ) ) return exception( E_ARGVAL );

  Real *dst = dstaddr;

  Size nx = dstlen[0];
  Size ny = dstlen[1];

  for ( Size iy = 0; iy < ny; iy++ ) {
    Coord y = c[0] + c[2] * iy;

    for ( Size ix = 0; ix < nx; ix++ ) {
      *dst++ -= c[1] * ix + y;
    }

  } /* end for iy */

  return E_NONE;

}
