/*----------------------------------------------------------------------------*
*
*  tomoseriesupdate.c  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseries.h"
#include "io.h"
#include "exception.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomoseriesUpdate
              (Tomoseries *series,
               Tomotilt *tilt)

{
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );

  Tomogeom *geom = malloc( series->tilt->images * sizeof(Tomogeom) );
  if ( geom == NULL ) return pushexception( E_MALLOC );

  status = TomogeomInit( tilt, series->A, series->b, geom );
  if ( exception( status ) ) goto error;

  status = TomometaWrite( series->meta, tilt, series->data->file );
  if ( exception( status ) ) goto error;

  status = TomometaUpdate( series->meta, tilt );
  if ( exception( status ) ) goto error;

  status = TomotiltDestroy( series->tilt );
  logexception( status );

  free( series->geom );

  series->geom = geom;
  series->tilt = tilt;
  series->data->image = tilt->tiltimage;

  return E_NONE;

  error: free( geom );

  return status;

}
