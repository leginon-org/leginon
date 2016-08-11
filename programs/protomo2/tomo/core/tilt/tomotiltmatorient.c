/*----------------------------------------------------------------------------*
*
*  tomotiltmatorient.c  -  tomography: tilt series
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
#include "mat3.h"
#include "mathdefs.h"


/* functions */

extern Status TomotiltMatOrient
              (const Coord euler[3],
               Coord A[3][3])

{
  Coord degtorad = Pi / 180;
  Coord e[3] = { 0, 0, 0 };
  Status status = E_NONE;

  if ( euler == NULL ) return exception( E_ARGVAL );
  if ( A == NULL ) return exception( E_ARGVAL );

  if ( euler[0] < TomotiltValMax ) e[0] = euler[0] * degtorad;
  if ( euler[1] < TomotiltValMax ) e[1] = euler[1] * degtorad;
  if ( euler[2] < TomotiltValMax ) e[2] = euler[2] * degtorad;

  Mat3Rot( e, A );

  return status;

}
