/*----------------------------------------------------------------------------*
*
*  mask_rect_2d_cmplx.c  -  array: mask operations
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

extern Status MaskRect2dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags)

{
  Cmplx *dst = addr;
  Coord B[2*2];
  Coord c[2], p[2];
  Coord r[2], q[2];

  if ( argcheck( len  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( w    == NULL ) ) return exception( E_ARGVAL );

  MaskSetupParam( 2, len, b, w, c, p, flags );

  if ( A == NULL ) {

    for ( Size y = 0; y < len[1]; y++ ) {

      q[1] = p[1] * ( y - c[1] );
      if ( q[1] < 0 ) q[1] = -q[1];

      for ( Size x = 0; x < len[0]; x++ ) {

        q[0] = p[0] * ( x - c[0] );
        if ( q[0] < 0 ) q[0] = -q[0];

        if ( flags & MaskModeInv ) {
          if ( ( q[0] <= 1 ) && ( q[1] <= 1 ) ) *dst = v;
        } else {
          if ( ( q[0] > 1 ) || ( q[1] > 1 ) ) *dst = v;
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

        if ( q[0] < 0 ) q[0] = -q[0];
        if ( q[1] < 0 ) q[1] = -q[1];

        if ( flags & MaskModeInv ) {
          if ( ( q[0] <= 1 ) && ( q[1] <= 1 ) ) *dst = v;
        } else {
          if ( ( q[0] > 1 ) || ( q[1] > 1 ) ) *dst = v;
        }

        dst++;

      } /* end for x */

    } /* end for y */

  }

  return E_NONE;

}
