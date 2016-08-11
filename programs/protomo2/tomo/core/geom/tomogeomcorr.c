/*----------------------------------------------------------------------------*
*
*  tomogeomcorr.c  -  tomography: tilt geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomogeom.h"
#include "mat2.h"
#include "exception.h"


/* functions */

extern Status TomogeomCorr
              (Coord Am[3][3],
               Coord Ap[3][2],
               Coord *alpha,
               Coord corr[2],
               Coord *beta)

{
  Coord C[2][2], U[2][2], S[2], V[2][2];
  Status status;

  if ( Am == NULL ) return pushexception( E_ARGVAL );
  if ( Ap == NULL ) return pushexception( E_ARGVAL );

  C[0][0] = Am[0][0]; C[0][1] = Am[0][1];
  C[1][0] = Am[1][0]; C[1][1] = Am[1][1];

  status = Mat2Inv( C, C, NULL );
  if ( pushexception( status ) ) return status;

  Mat2Mul( C, Ap, C );

  Mat2Svd( C, U, S, V );

  Coord a = Atan2( U[0][1], U[0][0] ) * 180 / Pi;
  Coord b = Atan2( V[1][0], V[0][0] ) * 180 / Pi;

  if ( alpha != NULL ) {
    *alpha = a + b;
  }
  if ( corr != NULL ) {
    corr[0] = S[0];
    corr[1] = S[1];
  }
  if ( beta != NULL ) {
    *beta  = b;
  }

  return E_NONE;

}
