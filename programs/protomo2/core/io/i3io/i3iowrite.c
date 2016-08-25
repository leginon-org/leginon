/*----------------------------------------------------------------------------*
*
*  i3iowrite.c  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3iocommon.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status I3ioWrite
              (I3io *i3io,
               int segm,
               Offset offs,
               Size size,
               const void *buf)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( offs < 0 ) ) return exception( E_ARGVAL );

  status = I3ioSet( i3io, segm, &offs, &size );
  if ( exception( status ) ) return status;

  Heap *heap = (Heap *)i3io;

  status = heap->proc->write( heap->data, offs, size, buf );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status I3ioWriteSegm
              (I3io *i3io,
               int segm,
               Size size,
               const void *buf)

{
  Offset off, siz;
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );

  if ( size > (Size)OffsetMaxSize ) return exception( E_I3IO_LEN );

  Heap *heap = (Heap *)i3io;

  status = HeapAccess( heap, segm, &off, &siz, NULL );
  if ( exception( status ) ) return status;

  if ( (Offset)size != siz ) return exception( E_I3IO_LEN );

  status = heap->proc->write( heap->data, off, size, buf );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status I3ioWriteAlloc
              (I3io *i3io,
               int segm,
               Size size,
               const void *buf,
               I3ioMeta meta)

{
  Offset off;
  Status status, stat;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );

  if ( size > (Size)OffsetMaxSize ) return exception( E_I3IO_LEN );

  Heap *heap = (Heap *)i3io;

  status = HeapAlloc( heap, segm, size, meta, &off );
  if ( exception( status ) ) return status;

  status = heap->proc->write( heap->data, off, size, buf );
  if ( exception( status ) ) goto error;

  return E_NONE;

  error:

  stat = HeapDealloc( heap, segm );
  logexception( stat );

  return status;

}
