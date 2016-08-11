/*----------------------------------------------------------------------------*
*
*  tomotilt.c  -  tomography: tilt series
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
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomotilt *TomotiltCreate
                 (const char *ident,
                  Size images,
                  Size axes,
                  Size orients,
                  Size files,
                  const EMparam *emparam)

{
  Status status;

  if ( ( ident == NULL ) || !*ident ) { pushexception( E_ARGVAL ); return NULL; }

  Tomotilt *tomotilt = malloc( sizeof(Tomotilt) );
  if ( tomotilt == NULL ) {
    status = exception( E_MALLOC ); goto error6;
  }

  Size length = strlen( ident ) + 1;
  tomotilt->tiltstrings = malloc( length );
  if ( tomotilt->tiltstrings == NULL ) {
    status = exception( E_MALLOC ); goto error6;
  } else {
    memcpy( tomotilt->tiltstrings, ident, length );
    tomotilt->strings = length;
  }

  if ( images ) {
    tomotilt->tiltimage = malloc( images * sizeof(TomotiltImage) );
    if ( tomotilt->tiltimage == NULL ) {
      status = exception( E_MALLOC ); goto error5;
    }
  } else {
    tomotilt->tiltimage = NULL;
  }

  if ( images ) {
    tomotilt->tiltgeom = malloc( images * sizeof(TomotiltGeom) );
    if ( tomotilt->tiltgeom == NULL ) {
      status = exception( E_MALLOC ); goto error4;
    }
  } else {
    tomotilt->tiltgeom = NULL;
  }

  if ( axes ) {
    tomotilt->tiltaxis = malloc( axes * sizeof(TomotiltAxis) );
    if ( tomotilt->tiltaxis == NULL ) {
      status = exception( E_MALLOC ); goto error3;
    }
  } else {
    tomotilt->tiltaxis = NULL;
  }

  if ( orients ) {
    tomotilt->tiltorient = malloc( orients * sizeof(TomotiltOrient) );
    if ( tomotilt->tiltorient == NULL ) {
      status = exception( E_MALLOC ); goto error2;
    }
  } else {
    tomotilt->tiltorient = NULL;
  }

  if ( files ) {
    tomotilt->tiltfile = malloc( files * sizeof(TomotiltFile) );
    if ( tomotilt->tiltfile == NULL ) {
      status = exception( E_MALLOC ); goto error1;
    }
  } else {
    tomotilt->tiltfile = NULL;
  }

  tomotilt->images = images;
  tomotilt->axes = axes;
  tomotilt->orients = orients;
  tomotilt->files = files;

  tomotilt->param.version = 3;
  tomotilt->param.cooref = TomotiltImageMax;
  tomotilt->param.euler[0] = CoordMax;
  tomotilt->param.euler[1] = CoordMax;
  tomotilt->param.euler[2] = CoordMax;
  tomotilt->param.origin[0] = CoordMax;
  tomotilt->param.origin[1] = CoordMax;
  tomotilt->param.origin[2] = CoordMax;
  tomotilt->param.pixel = 0;
  if ( emparam == NULL ) {
    memset( &tomotilt->param.emparam, 0, sizeof(EMparam) );
  } else {
    tomotilt->param.emparam = *emparam;
  }

  return tomotilt;

  error1: if ( tomotilt->tiltorient  != NULL ) free( tomotilt->tiltorient );
  error2: if ( tomotilt->tiltaxis    != NULL ) free( tomotilt->tiltaxis );
  error3: if ( tomotilt->tiltgeom    != NULL ) free( tomotilt->tiltgeom );
  error4: if ( tomotilt->tiltimage   != NULL ) free( tomotilt->tiltimage );
  error5: if ( tomotilt->tiltstrings != NULL ) free( tomotilt->tiltstrings );
  error6: pushexception( status );
  return NULL;

}


extern Status TomotiltDestroy
              (Tomotilt *tomotilt)

{

  if ( argcheck( tomotilt == NULL ) ) return exception( E_ARGVAL );

  if ( tomotilt->tiltimage != NULL ) {
    free( tomotilt->tiltimage );
  }

  if ( tomotilt->tiltgeom != NULL ) {
    free( tomotilt->tiltgeom );
  }

  if ( tomotilt->tiltaxis != NULL ) {
    free( tomotilt->tiltaxis );
  }

  if ( tomotilt->tiltorient != NULL ) {
    free( tomotilt->tiltorient );
  }

  if ( tomotilt->tiltfile != NULL ) {
    free( tomotilt->tiltfile );
  }

  if ( tomotilt->tiltstrings != NULL ) {
    free( tomotilt->tiltstrings );
  }

  free( tomotilt );

  return E_NONE;

}
