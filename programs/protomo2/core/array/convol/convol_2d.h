/*----------------------------------------------------------------------------*
*
*  convol_2d.h  -  array: convolution
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

/* template */

{
  const TYPE *src = srcaddr;
  const Real *krn = krnaddr;
  TYPE *dst = dstaddr;

  if ( argcheck( srclen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krn    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst    == NULL ) ) return exception( E_ARGVAL );

  if ( !krnlen[0] ) return exception( E_ARRAY_ZERO );
  if ( !krnlen[1] ) return exception( E_ARRAY_ZERO );

  Size nx = srclen[0];
  Size ny = srclen[1];

  Size mx = krnlen[0];
  Size my = krnlen[1];

  if ( nx < mx ) return exception( E_CONVOL_SIZE );
  if ( ny < my ) return exception( E_CONVOL_SIZE );

  Size lx = mx / 2, hx = mx - lx;
  Size ly = my / 2, hy = my - ly;

  for ( Size iy = 0; iy < ny; iy++ ) {

    Size iy0 = ( iy > ly ) ? iy - ly : 0;
    Size iyn = ( iy < ny - hy ) ? iy + hy : ny;

    Size ky0 = iy0 - ( iy - ly );

    iy0 *= nx; ky0 *= mx;
    iyn *= nx;

    for ( Size ix = 0; ix < nx; ix++ ) {

      Size ix0 = ( ix > lx ) ? ix - lx : 0;
      Size ixn = ( ix < nx - hx ) ? ix + hx : nx;

      Size kx0 = ix0 - ( ix - lx );

      Coord d = 0, n = 0;
      for ( Size y = iy0, ky = ky0; y < iyn; y += nx, ky += mx ) {
        for ( Size x = ix0, kx = kx0; x < ixn; x++, kx++ ) {
          Size i = y + x, k = ky + kx;
          d += src[i] * krn[k];
          n += krn[k];
        }
      }
      d /= n;
      if ( d < TYPEMIN ) {
        d = TYPEMIN;
      } else if ( d > TYPEMAX ) {
        d = TYPEMAX;
      }
      *dst++ = d;

    } /* end for ix */

  }  /* end for iy */

  return E_NONE;

}
