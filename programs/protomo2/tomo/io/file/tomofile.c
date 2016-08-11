/*----------------------------------------------------------------------------*
*
*  tomofile.c  -  series: tilt series image file handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomofile.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomofile *TomofileCreate
                 (const Tomotilt *tomotilt)

{
  Status status;

  if ( tomotilt == NULL ) { pushexception( E_ARGVAL ); return NULL; }

  Tomofile *tomofile = malloc( sizeof(Tomofile) );
  if ( tomofile == NULL ) { status = exception( E_MALLOC ); goto error0; }
  *tomofile = TomofileInitializer;

  Size files = tomotilt->files;
  tomofile->files = files;

  if ( !files ) return tomofile;

  TomofileDscr *dscr = malloc( files * sizeof(TomofileDscr) );
  if ( dscr == NULL ) { status = exception( E_MALLOC ); goto error1; }
  memset( dscr, 0, files * sizeof(TomofileDscr) );
  tomofile->dscr = dscr;

  TomofileIO *io = malloc( files * sizeof(TomofileIO) );
  if ( io == NULL ) { status = exception( E_MALLOC ); goto error2; }
  tomofile->io = io;

  char *string = malloc( tomotilt->strings );
  if ( string == NULL ) { status = exception( E_MALLOC ); goto error3; }
  memcpy( string, tomotilt->tiltstrings, tomotilt->strings );
  tomofile->string = string;
  tomofile->strings = tomotilt->strings;

  const TomotiltFile *tiltfile = tomotilt->tiltfile;

  for ( Size index = 0; index < files; index++, dscr++, io++, tiltfile++ ) {
    dscr->nameindex = tiltfile->nameindex;
    dscr->dim = tiltfile->dim;
    io->name = string + tiltfile->nameindex;
    int len = strlen( io->name );
    if ( len > tomofile->width ) tomofile->width = len;
    io->path = NULL;
    io->handle = NULL;
  }

  return tomofile;

  /* error handling */

  error3: free( io );
  error2: free( dscr );
  error1: free( tomofile );
  error0: pushexception( status );

  return NULL;

}


extern Status TomofileDestroy
              (Tomofile *tomofile)

{
  Status status = E_NONE;

  if ( argcheck( tomofile == NULL ) ) return exception( E_ARGVAL );

  status = TomofileFinal( tomofile );
  logexception ( status );

  if ( tomofile->io != NULL ) free( tomofile->io );
  if ( tomofile->dscr != NULL ) free( tomofile->dscr );
  if ( tomofile->string != NULL ) free( (char *)tomofile->string );

  free( tomofile );

  return E_NONE;

}
