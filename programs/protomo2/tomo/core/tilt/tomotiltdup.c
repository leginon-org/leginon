/*----------------------------------------------------------------------------*
*
*  tomotiltdup.c  -  tomography: tilt series
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
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomotilt *TomotiltDup
                 (const Tomotilt *tomotilt)

{
  Tomotilt *tomotiltdup;

  if ( tomotilt == NULL ) {
    pushexception( E_ARGVAL ); return NULL;
  }

  tomotiltdup = malloc( sizeof(Tomotilt) );
  if ( tomotiltdup == NULL ) {
    pushexception( E_MALLOC ); return NULL;
  }
  tomotiltdup->param = tomotilt->param;

  if ( tomotilt->strings ) {
    tomotiltdup->strings = tomotilt->strings;
    tomotiltdup->tiltstrings = malloc( tomotilt->strings );
    if ( tomotiltdup->tiltstrings == NULL ) {
      pushexception( E_MALLOC ); goto error6;
    } else {
      memcpy( tomotiltdup->tiltstrings, tomotilt->tiltstrings, tomotilt->strings );
    }
  } else {
    tomotiltdup->strings = 0;
    tomotiltdup->tiltstrings = NULL;
  }

  if ( tomotilt->images ) {
    tomotiltdup->images = tomotilt->images;
    tomotiltdup->tiltimage = malloc( tomotilt->images * sizeof(TomotiltImage) );
    if ( tomotiltdup->tiltimage == NULL ) {
      pushexception( E_MALLOC ); goto error5;
    } else {
      memcpy( tomotiltdup->tiltimage, tomotilt->tiltimage, tomotilt->images * sizeof(TomotiltImage) );
    }
  } else {
    tomotiltdup->images = 0;
    tomotiltdup->tiltimage = NULL;
  }

  if ( tomotilt->images ) {
    tomotiltdup->tiltgeom = malloc( tomotilt->images * sizeof(TomotiltGeom) );
    if ( tomotiltdup->tiltgeom == NULL ) {
      pushexception( E_MALLOC ); goto error4;
    } else {
      memcpy( tomotiltdup->tiltgeom, tomotilt->tiltgeom, tomotilt->images * sizeof(TomotiltGeom) );
    }
  } else {
    tomotiltdup->tiltgeom = NULL;
  }

  if ( tomotilt->axes ) {
    tomotiltdup->axes = tomotilt->axes;
    tomotiltdup->tiltaxis = malloc( tomotilt->axes * sizeof(TomotiltAxis) );
    if ( tomotiltdup->tiltaxis == NULL ) {
      pushexception( E_MALLOC ); goto error3;
    } else {
      memcpy( tomotiltdup->tiltaxis, tomotilt->tiltaxis, tomotilt->axes * sizeof(TomotiltAxis) );
    }
  } else {
    tomotiltdup->axes = 0;
    tomotiltdup->tiltaxis = NULL;
  }

  if ( tomotilt->orients ) {
    tomotiltdup->orients = tomotilt->orients;
    tomotiltdup->tiltorient = malloc( tomotilt->orients * sizeof(TomotiltOrient) );
    if ( tomotiltdup->tiltorient == NULL ) {
      pushexception( E_MALLOC ); goto error2;
    } else {
      memcpy( tomotiltdup->tiltorient, tomotilt->tiltorient, tomotilt->orients * sizeof(TomotiltOrient) );
    }
  } else {
    tomotiltdup->orients = 0;
    tomotiltdup->tiltorient = NULL;
  }

  if ( tomotilt->files ) {
    tomotiltdup->files = tomotilt->files;
    tomotiltdup->tiltfile = malloc( tomotilt->files * sizeof(TomotiltFile) );
    if ( tomotiltdup->tiltfile == NULL ) {
      pushexception( E_MALLOC ); goto error1;
    } else {
      memcpy( tomotiltdup->tiltfile, tomotilt->tiltfile, tomotilt->files * sizeof(TomotiltFile) );
    }
  } else {
    tomotiltdup->files = 0;
    tomotiltdup->tiltfile = NULL;
  }

  return tomotiltdup;

  error1: if ( tomotiltdup->tiltorient  != NULL ) free( tomotiltdup->tiltorient );
  error2: if ( tomotiltdup->tiltaxis    != NULL ) free( tomotiltdup->tiltaxis );
  error3: if ( tomotiltdup->tiltgeom    != NULL ) free( tomotiltdup->tiltgeom );
  error4: if ( tomotiltdup->tiltimage   != NULL ) free( tomotiltdup->tiltimage );
  error5: if ( tomotiltdup->tiltstrings != NULL ) free( tomotiltdup->tiltstrings );
  error6: free( tomotiltdup);
  return NULL;

}
