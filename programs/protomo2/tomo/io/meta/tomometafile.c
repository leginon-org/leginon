/*----------------------------------------------------------------------------*
*
*  tomometafile.c  -  series: tomography: tilt series
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
#include "heapproc.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomometa *TomometaCreate
                 (const char *path,
                  const char *prfx,
                  const Tomotilt *tilt,
                  Tomoflags flags)

{
  Status status;

  if ( argcheck( tilt == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomometa *meta = malloc( sizeof(Tomometa) );
  if ( meta == NULL ) { pushexception( E_MALLOC ); return NULL; }
  meta->cycle = ( flags & TomoCycle ) ? 0 : -1;
  meta->hdrwr = False;

  I3ioParam *iopar = NULL;
  char *metapath = TomometaPath( path, prfx );
  if ( metapath == NULL ) goto error1;

  if ( flags & TomoNewonly ) {
    meta->mode = IONew | IOWr | IORd;
    meta->handle = I3ioCreateOnly( metapath, iopar );
    if ( testcondition( meta->handle == NULL ) ) goto error2;
  } else {
    meta->mode = IOCre | IOWr | IORd;
    meta->handle = I3ioCreate( metapath, iopar );
    if ( testcondition( meta->handle == NULL ) ) goto error2;
  }

  status = TomometaInit( meta, tilt );
  if ( pushexception( status ) ) goto error3;

  status = I3ioClose( meta->handle, E_NONE );
  if ( pushexception( status ) ) goto error2;

  meta->handle = I3ioOpenUpdate( metapath, iopar );
  if ( testcondition( meta->handle == NULL ) ) goto error2;

  free( metapath );

  return meta;

  error3: I3ioClose( meta->handle, status );
  error2: free( metapath );
  error1: free( meta );

  return NULL;

}


extern Tomometa *TomometaOpen
                 (const char *path,
                  const char *prfx,
                  Tomotilt **tiltptr,
                  Tomofile **fileptr,
                  Tomoflags flags)

{
  I3ioParam *iopar = NULL;
  Status status;

  Tomometa *meta = malloc( sizeof(Tomometa) );
  if ( meta == NULL ) { pushexception( E_MALLOC ); return NULL; }

  char *metapath = TomometaPath( path, prfx );
  if ( metapath == NULL ) goto error1;

  if ( flags & TomoReadonly ) {
    meta->mode = IOOld | IORd;
    meta->handle = I3ioOpenReadOnly( metapath, iopar );
    if ( testcondition( meta->handle == NULL ) ) goto error2;
    flags &= ~TomoCycle;
  } else {
    meta->mode = IOOld | IOWr | IORd;
    meta->handle = I3ioOpenUpdate( metapath, iopar );
    if ( testcondition( meta->handle == NULL ) ) goto error2;
  }
  meta->hdrwr = True;

  free( metapath );

  status = TomometaSetup( meta, tiltptr, fileptr, flags );
  if ( exception( status ) ) goto error1;

  return meta;

  error2: free( metapath );
  error1: free( meta );

  return NULL;

}


extern Status TomometaClose
              (Tomometa *meta,
               Status fail)

{
  Status stat, status = E_NONE;

  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  if ( fail == E_HEAPPROC_DEL ) goto exit;

  if ( !meta->hdrwr && !fail ) return pushexception( E_TOMOMETA );

  if ( meta->mode & ( IONew | IOCre ) ) {

    I3ioMeta iometa = 0;
    strncpy( (char *)&iometa, meta->ident, sizeof(iometa) );
    status = I3ioMetaSet( meta->handle, 4, iometa );
    if ( pushexception( status ) ) fail = E_HEAPPROC_DEL;

  } else {

    fail = E_NONE;

  }

  exit:

  stat = I3ioClose( meta->handle, fail );
  if ( status ) {
    logexception( stat );
  } else {
    status = pushexception( stat );
  }

  free( meta );

  return status;

}
