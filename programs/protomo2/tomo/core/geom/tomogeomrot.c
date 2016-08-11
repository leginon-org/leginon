/*----------------------------------------------------------------------------*
*
*  tomogeomrot.c  -  tomography: tilt geometry
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

extern Status TomogeomRot
              (Coord Am[3][3],
               Coord Ap[3][2],
               Coord *alpha)

{
  Coord C[2][2];
  Status status;

  if ( Am == NULL ) return pushexception( E_ARGVAL );
  if ( Ap == NULL ) return pushexception( E_ARGVAL );

  C[0][0] = Am[0][0]; C[0][1] = Am[0][1];
  C[1][0] = Am[1][0]; C[1][1] = Am[1][1];

  status = Mat2Inv( C, C, NULL );
  if ( pushexception( status ) ) return status;

  Mat2Mul( C, Ap, C );

  Coord a = Atan2( C[0][1], C[0][0] ) * 180 / Pi;

  if ( alpha != NULL ) {
    *alpha = a;
  }

  return E_NONE;

}
