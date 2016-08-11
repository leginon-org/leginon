/*----------------------------------------------------------------------------*
*
*  tomotiltsort.c  -  tomography: tilt series
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

extern void TomotiltSortAngle
            (Tomotilt *tomotilt)

{
  uint32_t *cooref;

  if ( tomotilt == NULL ) return;

  for ( Size index = 0; index < tomotilt->images; index++ ) {

    Size k = index;

    for ( Size j = index + 1; j < tomotilt->images; j++ ) {
      if ( tomotilt->tiltgeom[j].theta < tomotilt->tiltgeom[k].theta ) k = j;
    }

    if ( k > index ) {

      TomotiltImage image = tomotilt->tiltimage[index];
      tomotilt->tiltimage[index] = tomotilt->tiltimage[k];
      tomotilt->tiltimage[k] = image;

      TomotiltGeom geom = tomotilt->tiltgeom[index];
      tomotilt->tiltgeom[index] = tomotilt->tiltgeom[k];
      tomotilt->tiltgeom[k] = geom;

      cooref = &tomotilt->tiltaxis[geom.axisindex].cooref;
      if ( *cooref == index ) {
        *cooref = k;
      } else if ( *cooref == k ) {
        *cooref = index;
      }

      cooref = &tomotilt->param.cooref;
      if ( *cooref == index ) {
        *cooref = k;
      } else if ( *cooref == k ) {
        *cooref = index;
      }

    }

  }

}


extern void TomotiltSortNumber
            (Tomotilt *tomotilt)

{
  uint32_t *cooref;

  if ( tomotilt == NULL ) return;

  for ( Size index = 0; index < tomotilt->images; index++ ) {

    Size k = index;

    for ( Size j = index + 1; j < tomotilt->images; j++ ) {
      if ( tomotilt->tiltimage[j].number < tomotilt->tiltimage[k].number ) k = j;
    }

    if ( k > index ) {

      TomotiltImage image = tomotilt->tiltimage[index];
      tomotilt->tiltimage[index] = tomotilt->tiltimage[k];
      tomotilt->tiltimage[k] = image;

      TomotiltGeom geom = tomotilt->tiltgeom[index];
      tomotilt->tiltgeom[index] = tomotilt->tiltgeom[k];
      tomotilt->tiltgeom[k] = geom;

      cooref = &tomotilt->tiltaxis[geom.axisindex].cooref;
      if ( *cooref == index ) {
        *cooref = k;
      } else if ( *cooref == k ) {
        *cooref = index;
      }

      cooref = &tomotilt->param.cooref;
      if ( *cooref == index ) {
        *cooref = k;
      } else if ( *cooref == k ) {
        *cooref = index;
      }

    }

  }

}
