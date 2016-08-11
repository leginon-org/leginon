/*----------------------------------------------------------------------------*
*
*  mask_rect_apod_2d_real.c  -  array: mask operations
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

extern Status MaskRectApod2dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Real v,
               MaskFlags flags)

{
  Real *dst = addr;
  Coord B[2*2];
  Coord c[2], p[2], t[2];
  Coord r[2], q[2];

  if ( argcheck( len  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( w    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( s    == NULL ) ) return exception( E_ARGVAL );

  MaskSetupParamApod( 2, len, b, w, s, c, p, t, flags );

  if ( A == NULL ) {

    for ( Size y = 0; y < len[1]; y++ ) {

      q[1] = p[1] * ( y - c[1] );

      for ( Size x = 0; x < len[0]; x++ ) {

        q[0] = p[0] * ( x - c[0] );

        Coord f = 1;
        if ( w[0] > 0 ) {
          if ( t[0] > 0 ) {
            MaskErfEval( f, q[0], t[0] );
          } else if ( ( q[0] < -1 ) || ( q[0] > 1 ) ) {
            f = 0;
          }
        }
        if ( ( w[1] > 0 ) && ( f != 0 ) ) {
          if ( t[1] > 0 ) {
            Coord f1;
            MaskErfEval( f1, q[1], t[1] );
            f *= f1;
          } else if ( ( q[1] < -1 ) || ( q[1] > 1 ) ) {
            f = 0;
          }
        }
        if ( flags & MaskModeInv ) f = 1.0 - f;

        *dst = f * ( *dst - v ) + v;

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

        Coord f = 1;
        if ( w[0] > 0 ) {
          if ( t[0] > 0 ) {
            MaskErfEval( f, q[0], t[0] );
          } else if ( ( q[0] < -1 ) || ( q[0] > 1 ) ) {
            f = 0;
          }
        }
        if ( ( w[1] > 0 ) && ( f != 0 ) ) {
          if ( t[1] > 0 ) {
            Coord f1;
            MaskErfEval( f1, q[1], t[1] );
            f *= f1;
          } else if ( ( q[1] < -1 ) || ( q[1] > 1 ) ) {
            f = 0;
          }
        }
        if ( flags & MaskModeInv ) f = 1.0 - f;

        *dst = f * ( *dst - v ) + v;

        dst++;

      } /* end for x */

    } /* end for y */

  }

  return E_NONE;

}
