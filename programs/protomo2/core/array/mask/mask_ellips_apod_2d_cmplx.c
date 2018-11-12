/*----------------------------------------------------------------------------*
*
*  mask_ellips_apod_2d_cmplx.c  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "maskcommon.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status MaskEllipsApod2dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Cmplx v,
               MaskFlags flags)

{
  Cmplx *dst = addr;
  Coord B[2*2];
  Coord c[2], p[2], t[2];
  Coord r[2], q[2];
  Cmplx *dst0 = NULL;

  if ( argcheck( len  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( w    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( s    == NULL ) ) return exception( E_ARGVAL );

  MaskSetupParamApod( 2, len, b, w, s, c, p, t, flags );
  if ( w[0] > 0 ) { t[0] = 1 + t[0]; t[0] *= t[0]; }
  if ( w[1] > 0 ) { t[1] = 1 + t[1]; t[1] *= t[1]; }

  if ( A == NULL ) {

    for ( Size y = 0; y < len[1]; y++ ) {

      q[1] = p[1] * ( y - c[1] ); q[1] *= q[1];

      for ( Size x = 0; x < len[0]; x++ ) {

        q[0] = p[0] * ( x - c[0] ); q[0] *= q[0];

        Coord q2 = Sqrt( q[0] + q[1] );

        if ( q2 < 10 * CoordEPS ) {

          dst0 = dst;

        } else {

          Coord s2 = q[0]*t[0] + q[1]*t[1];
          s2 = Sqrt( s2 ) / q2 - 1;
          Coord f;
          MaskErfEval( f, q2, s2 );
          if ( flags & MaskModeInv ) f = 1.0 - f;

          Cset( *dst, f * ( Re( *dst ) - Re( v ) ) + Re( v ), f * ( Im( *dst ) - Im( v ) ) + Im( v ) );

        }

        dst++;

      } /* end for x */

    } /* end for y */

  } else {

    MaskSetupMat( 2, A, p, B );

    for ( Size y = 0; y < len[1]; y++ ) {

      r[1] = y - c[1];

      for ( Size x = 0; x < len[0]; x++ ) {

        r[0] = x - c[0];

        MaskMulVec2( B, r, q );

        q[0] *= q[0]; q[1] *= q[1];

        Coord q2 = Sqrt( q[0] + q[1] );

        if ( q2 < 10 * CoordEPS ) {

          dst0 = dst;

        } else {

          Coord s2 = q[0]*t[0] + q[1]*t[1];
          s2 = Sqrt( s2 ) / q2 - 1;
          Coord f;
          MaskErfEval( f, q2, s2 );
          if ( flags & MaskModeInv ) f = 1.0 - f;

          Cset( *dst, f * ( Re( *dst ) - Re( v ) ) + Re( v ), f * ( Im( *dst ) - Im( v ) ) + Im( v ) );

        }

        dst++;

      } /* end for x */

    } /* end for y */

  }

  if ( dst0 != NULL ) {
    Cset( dst0[0], 0.5 * ( Re( dst0[-1] ) + Re( dst0[1] ) ), 0.5 * ( Im( dst0[-1] ) + Im( dst0[1] ) ) ); 
  }

  return E_NONE;

}
