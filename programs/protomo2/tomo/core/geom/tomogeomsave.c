/*----------------------------------------------------------------------------*
*
*  tomogeomsave.c  -  tomography: tilt geometry
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
#include "mat3.h"
#include "exception.h"
#include <string.h>


/* functions */

extern Status TomogeomSave
              (Coord A[3][3],
               Coord Am[3][3],
               Coord Ap[3][2],
               Coord origin[3],
               Bool fulltransf,
               Size index,
               Tomotilt *tilt)

{
  Coord d[3];
  Status status;

  if ( A == NULL ) return pushexception( E_ARGVAL );
  if ( Am == NULL ) return pushexception( E_ARGVAL );
  if ( Ap == NULL ) return pushexception( E_ARGVAL );
  if ( tilt == NULL ) return pushexception( E_ARGVAL );

  if ( index >= tilt->images ) return pushexception( E_TOMOGEOM );

  TomotiltGeom *tiltgeom = tilt->tiltgeom + index;

  if ( ( ( Ap[0][0] == 0 ) && ( Ap[0][1] == 0 ) ) || ( ( Ap[1][0] == 0 ) && ( Ap[1][1] == 0 ) ) ) {

    tiltgeom->corr[0] = tiltgeom->corr[1] = 0;

  } else {

    if ( fulltransf ) {

      status = TomogeomCorr( Am, Ap, &tiltgeom->alpha, tiltgeom->corr, &tiltgeom->beta );
      if ( exception( status ) ) return status;

    } else {

      status = TomogeomRot( Am, Ap, &tiltgeom->alpha );
      if ( exception( status ) ) return status;

      tiltgeom->corr[0] = tiltgeom->corr[1] = 0;

    }

    Mat3TranspMulVec( A, origin, d );

    tiltgeom->origin[0] = Ap[2][0] - d[0];
    tiltgeom->origin[1] = Ap[2][1] - d[1];

  }

  return E_NONE;

}
