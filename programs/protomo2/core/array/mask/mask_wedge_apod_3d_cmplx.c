/*----------------------------------------------------------------------------*
*
*  mask_wedge_apod_3d_cmplx.c  -  array: mask operations
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

extern Status MaskWedgeApod3dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags)

{
  Cmplx *dst = addr;
  Coord cosm, sinm;
  Coord cosp, sinp;
  Coord w2[3] = { 2, 2, 2 };
  Coord ap[3] = { 0, 0, 0 };
  Coord B[3*3];
  Coord c[3], p[3], t[3];
  Coord r[3], q[3];

  if ( argcheck( len  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( w    == NULL ) ) return exception( E_ARGVAL );

  if ( ( w[0] <= -Pi/2 ) || ( w[0] >= Pi/2 ) || ( w[1] <= -Pi/2 ) || ( w[1] >= Pi/2 ) ) {
    return exception( E_ARGVAL );
  }
  if ( w[0] >= w[1] ) return exception( E_ARGVAL );
  cosm = Cos( w[0] ); sinm = Sin( w[0] );
  cosp = Cos( w[1] ); sinp = Sin( w[1] );
  ap[2] = ( w[2] < 0.25 ) ? 0.25 : w[2];

  MaskSetupParamApod( 3, len, b, w2, ap, c, p, t, flags & ~MaskModeFract );

  if ( A == NULL ) {

    for ( Size z = 0; z < len[2]; z++ ) {

      r[2] = p[2] * ( z - c[2] );

      for ( Size y = 0; y < len[1]; y++ ) {

        r[1] = p[1] * ( y - c[1] );

        for ( Size x = 0; x < len[0]; x++ ) {

          r[0] = p[0] * ( x - c[0] );

          q[0] = r[0];
          if ( r[1] < 0 ) {
            q[1] = -r[1];
            q[2] = -r[2];
          } else {
            q[1] = r[1];
            q[2] = r[2];
          }
          Coord dm = sinm * q[1] - cosm * q[2];
          Coord dp = sinp * q[1] - cosp * q[2];
          dm = -dm / t[2];
          dp =  dp / t[2];
          Coord f = 0.25 * ( MaskErf( dm ) + 1 ) * ( MaskErf( dp ) + 1 );
          if ( ~flags & MaskModeInv ) f = 1.0 - f;

          Cset( *dst, f * ( Re( *dst ) - Re( v ) ) + Re( v ), f * ( Im( *dst ) - Im( v ) ) + Im( v ) );

          dst++;

        } /* end for x */

      } /* end for y */

    } /* end for z */

  } else {

    MaskSetupMat( 3, A, p, B );

    for ( Size z = 0; z < len[2]; z++ ) {

      r[2] = z - c[2];

      for ( Size y = 0; y < len[1]; y++ ) {

        r[1] = y - c[1];

        for ( Size x = 0; x < len[0]; x++ ) {

          r[0] = x - c[0];

          MaskMulVec3( B, r, q );

          if ( q[1] < 0 ) {
            q[1] = -q[1];
            q[2] = -q[2];
          }
          Coord dm = sinm * q[1] - cosm * q[2];
          Coord dp = sinp * q[1] - cosp * q[2];
          dm = -dm / t[2];
          dp =  dp / t[2];
          Coord f = 0.25 * ( MaskErf( dm ) + 1 ) * ( MaskErf( dp ) + 1 );
          if ( ~flags & MaskModeInv ) f = 1.0 - f;

          Cset( *dst, f * ( Re( *dst ) - Re( v ) ) + Re( v ), f * ( Im( *dst ) - Im( v ) ) + Im( v ) );

          dst++;

        } /* end for x */

      } /* end for y */

    } /* end for z */

  }

  return E_NONE;

}
