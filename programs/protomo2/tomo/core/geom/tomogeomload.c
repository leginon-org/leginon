/*----------------------------------------------------------------------------*
*
*  tomogeomload.c  -  tomography: tilt geometry
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
#include "mat3.h"
#include "exception.h"


/* functions */

extern Status TomogeomLoad
              (const Tomotilt *tilt,
               Size index,
               Coord A[3][3],
               const Coord b[3],
               Tomogeom *geom)

{
  Coord Aa[3][3];
  Coord d[3];
  Status status;

  if ( tilt == NULL ) return pushexception( E_ARGVAL );
  if ( geom == NULL ) return pushexception( E_ARGVAL );

  if ( index >= tilt->images ) return pushexception( E_TOMOGEOM );

  if ( ( A != NULL ) && ( A[0][0] == CoordMax ) ) A = NULL;

  geom->origin[0] = tilt->param.origin[0];
  geom->origin[1] = tilt->param.origin[1];
  geom->origin[2] = tilt->param.origin[2];
  if ( ( b != NULL ) && ( b[0] != CoordMax ) ) {
    geom->origin[0] += b[0];
    geom->origin[1] += b[1];
    geom->origin[2] += b[2];
  }

  const TomotiltGeom *tiltgeom = tilt->tiltgeom + index;
  const TomotiltAxis *axis = tilt->tiltaxis + tiltgeom->axisindex;
  const TomotiltOrient *orient = tilt->tiltorient + tiltgeom->orientindex;

  status = TomotiltMat( tilt->param.euler, axis, orient, tiltgeom, A, geom->A, geom->Am, geom->Af, False );
  if ( pushexception( status ) ) return status;

  Mat3TranspMulVec( geom->A, geom->origin, d );

  geom->Ap[0][0] = geom->A[0][0];              geom->Ap[0][1] = geom->A[0][1];
  geom->Ap[1][0] = geom->A[1][0];              geom->Ap[1][1] = geom->A[1][1];
  geom->Ap[2][0] = tiltgeom->origin[0] + d[0]; geom->Ap[2][1] = tiltgeom->origin[1] + d[1];

  if ( tiltgeom->corr[0] > 0 ) {

    status = TomotiltMat( tilt->param.euler, axis, orient, tiltgeom, A, Aa, NULL, NULL, True );
    if ( pushexception( status ) ) return status;

    Mat3TranspMulVec( Aa, geom->origin, d );

    geom->Aa[0][0] = Aa[0][0];                   geom->Aa[0][1] = Aa[0][1];
    geom->Aa[1][0] = Aa[1][0];                   geom->Aa[1][1] = Aa[1][1];
    geom->Aa[2][0] = tiltgeom->origin[0] + d[0]; geom->Aa[2][1] = tiltgeom->origin[1] + d[1];

  } else {

    geom->Aa[0][0] = 0; geom->Aa[0][1] = 0;
    geom->Aa[1][0] = 0; geom->Aa[1][1] = 0;
    geom->Aa[2][0] = 0; geom->Aa[2][1] = 0;

  }

  return E_NONE;

}
