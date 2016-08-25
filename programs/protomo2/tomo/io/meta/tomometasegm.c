/*----------------------------------------------------------------------------*
*
*  tomometasegm.c  -  series: tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomometacommon.h"
#include "i3ionest.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Tomometa *TomometaCreateSegm
                 (I3io *i3io,
                  int segm,
                  const Tomotilt *tilt,
                  Tomoflags flags)

{
  Status status;

  if ( argcheck( tilt == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomometa *meta = malloc( sizeof(Tomometa) );
  if ( meta == NULL ) { pushexception( E_MALLOC ); return NULL; }

  if ( flags & TomoNewonly ) {
    meta->handle = I3ioCreateOnlyNested( i3io, segm, 0 );
    if ( testcondition( meta->handle == NULL ) ) goto error1;
  } else {
    meta->handle = I3ioCreateNested( i3io, segm, 0 );
    if ( testcondition( meta->handle == NULL ) ) goto error1;
  }

  meta->cycle = ( flags & TomoCycle ) ? 0 : -1;
  meta->mode = I3ioGetMode( meta->handle );
  meta->hdrwr = False;

  status = TomometaInit( meta, tilt );
  if ( pushexception( status ) ) goto error2;

  status = I3ioClose( meta->handle, E_NONE );
  if ( pushexception( status ) ) goto error2;

  meta->handle = I3ioOpenUpdateNested( i3io, segm, 0 );
  if ( testcondition( meta->handle == NULL ) ) goto error1;

  return meta;

  error2: I3ioClose( meta->handle, status );
  error1: free( meta );

  return NULL;

}


extern Tomometa *TomometaOpenSegm
                 (I3io *i3io,
                  int segm,
                  Tomotilt **tiltptr,
                  Tomofile **fileptr,
                  Tomoflags flags)

{
  Status status;

  Tomometa *meta = malloc( sizeof(Tomometa) );
  if ( meta == NULL ) { pushexception( E_MALLOC ); return NULL; }

  if ( flags & TomoReadonly ) {
    meta->handle = I3ioOpenReadOnlyNested( i3io, segm, NULL );
    if ( testcondition( meta->handle == NULL ) ) goto error;
  } else {
    meta->handle = I3ioOpenUpdateNested( i3io, segm, NULL );
    if ( testcondition( meta->handle == NULL ) ) goto error;
  }

  meta->mode = I3ioGetMode( meta->handle );
  meta->hdrwr = True;

  if ( ~meta->mode & IOWr ) flags &= ~TomoCycle;

  status = TomometaSetup( meta, tiltptr, fileptr, flags );
  if ( exception( status ) ) goto error;

  return meta;

  error: free( meta );

  return NULL;

}
