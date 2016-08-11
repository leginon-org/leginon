/*----------------------------------------------------------------------------*
*
*  tomotiltcooref.c  -  tomography: tilt series
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
#include "exception.h"


/* functions */

extern void TomotiltSetCooref
            (Tomotilt *tomotilt)

{

  if ( tomotilt == NULL ) return;

  TomotiltAxis *tiltaxis = tomotilt->tiltaxis;
  TomotiltGeom *tiltgeom = tomotilt->tiltgeom;

  for ( Size axis = 0; axis < tomotilt->axes; axis++ ) {

    if ( tiltaxis[axis].cooref == TomotiltImageMax ) {

      Coord thetamin = CoordMax;
      for ( Size index = 0; index < tomotilt->images; index++ ) {
        if ( tiltgeom[index].axisindex == axis ) {
          Coord theta = fabs( tiltgeom[index].theta );
          if ( theta < thetamin ) {
            thetamin = theta;
            tiltaxis[axis].cooref = index;
          }
        }
      }

    }

  }

}
