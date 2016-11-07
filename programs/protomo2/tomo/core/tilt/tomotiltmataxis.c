/*----------------------------------------------------------------------------*
*
*  tomotiltmataxis.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotilt.h"
#include "base.h"
#include "exception.h"
#include "mat2.h"
#include "mat3.h"
#include "mathdefs.h"


/* functions */

extern Status TomotiltMatAxis
              (const Coord euler[3],
               const TomotiltAxis *axis,
               const TomotiltOrient *orient,
               Coord A0[3][3],
               Coord A[3][3])

{
  Coord degtorad = Pi/180;
  Coord R[3][3];

  if ( euler == NULL ) return exception( E_ARGVAL );
  if ( axis == NULL ) return exception( E_ARGVAL );
  if ( orient == NULL ) return exception( E_ARGVAL );
  if ( A == NULL ) return exception( E_ARGVAL );

  Coord phi = axis->phi * degtorad;
  Coord elev = -axis->theta * degtorad; /* elevation: clockwise rotation */
  Mat3RotZ( phi, R );
  Mat3RotY( elev, A );
  Mat3Mul( A, R, R );
  Mat3Transp( R, A );
  TomotiltMatOrient( orient->euler, R );
  Mat3Mul( R, A, A );
  TomotiltMatOrient( euler, R );
  Mat3Mul( R, A, A );
  if ( A0 != NULL ) {
    Mat3Mul( A0, A, A );
  }

  return E_NONE;

}


extern Status TomotiltMatAxis2
              (const TomotiltAxis *axis,
               const TomotiltGeom *geom,
               Coord Ap[2][2])

{
  Coord degtorad = Pi/180;

  if ( argcheck( axis == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( Ap == NULL ) ) return exception( E_ARGVAL );

  Coord rot = ( axis->phi + geom->alpha ) * degtorad;
  Mat2Rot( &rot, Ap );

  if ( geom->scale > 0 ) {
    Coord scale = geom->scale;
    Ap[0][0] *= scale; Ap[0][1] *= scale;
    Ap[1][0] *= scale; Ap[1][1] *= scale;
  }

  return E_NONE;

}
