/*----------------------------------------------------------------------------*
*
*  tomodata.c  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomodatacommon.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomodata *TomodataCreate
                 (Tomotilt *tilt,
                  Tomofile *file)

{

  if ( argcheck( tilt == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( file == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomodata *data = malloc( sizeof(Tomodata) );
  if ( data == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *data = TomodataInitializer;

  data->images = tilt->images;
  data->image = tilt->tiltimage;
  data->file = file;

  data->dscr = TomodataDscrCreate( data );
  if ( data->dscr == NULL ) { pushexception( E_MALLOC ); goto error; }

  return data;

  error: free( data );

  return NULL;

}


extern Status TomodataDestroy
              (Tomodata *data,
               Status fail)

{
  Status stat, status = E_NONE;

  if ( data->cache != NULL ) {
    stat = TomocacheDestroy( data->cache, fail );
    if ( exception( stat ) ) status = stat;
  }

  if ( data->file != NULL ) {
    stat = TomofileDestroy( data->file );
    if ( exception( stat ) ) status = stat;
  }

  if ( data->dscr != NULL ) {
    free( data->dscr );
  }

  free( data );

  return status;

}
