/*----------------------------------------------------------------------------*
*
*  tomometasave.c  -  series: tomography: tilt series
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
#include "i3ionest.h"
#include "exception.h"
#include <string.h>


/* functions */

static Status TomometaCopySegm
              (const Tomometa *meta,
               I3io *i3io)

{
  Size size;
  Status status, stat;

  int cycle = ( meta->cycle < 0 ) ? 0 : meta->cycle;

  for ( int segm = 0; segm < OFFS + ( cycle + 1 ) * BLOCK; segm++ ) {

    void *buf = I3ioBeginReadSegm( meta->handle, segm, &size );
    status = testcondition( buf == NULL );
    if ( status ) return status;

    status = I3ioWriteAlloc( i3io, segm, size, buf, 0 );

    stat = I3ioEndReadSegm( meta->handle, segm, buf );

    if ( pushexception( status ) ) return status;

    if ( pushexception( stat ) ) return stat;

  }

  I3ioMeta iometa = 0;
  strncpy( (char *)&iometa, meta->ident, sizeof(iometa) );

  status = I3ioMetaSet( i3io, 4, iometa );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}


extern Status TomometaSave
              (const Tomometa *meta,
               const char *path)

{
  Status status, stat;

  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  if ( ( path == NULL ) || !*path ) return pushexception( E_ARGVAL );

  I3io *i3io = I3ioCreateOnly( path, NULL );
  status = testcondition( i3io == NULL );
  if ( status ) return status;

  status = TomometaCopySegm( meta, i3io );
  pushexception( status );

  stat = I3ioClose( i3io, status );
  if ( status ) {
    logexception( stat );
  } else {
    status = pushexception( stat );
  }

  return status;

}


extern Status TomometaSaveSegm
              (const Tomometa *meta,
               I3io *i3io,
               int segm)

{
  Status status, stat;

  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( i3io == NULL ) ) return pushexception( E_ARGVAL );

  I3io *nest = I3ioCreateOnlyNested( i3io, segm, 0 );
  status = testcondition( nest == NULL );
  if ( status ) return status;

  status = TomometaCopySegm( meta, nest );
  pushexception( status );

  stat = I3ioClose( nest, status );
  if ( status ) {
    logexception( stat );
  } else {
    status = pushexception( stat );
  }


  return status;

}
