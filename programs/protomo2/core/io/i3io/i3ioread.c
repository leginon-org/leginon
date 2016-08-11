/*----------------------------------------------------------------------------*
*
*  i3ioread.c  -  io: i3 input/output
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

extern Status I3ioRead
              (I3io *i3io,
               int segm,
               Offset offs,
               Size size,
               void *buf)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( offs < 0 ) ) return exception( E_ARGVAL );

  status = I3ioSet( i3io, segm, &offs, &size );
  if ( exception( status ) ) return status;

  Heap *heap = (Heap *)i3io;

  status = heap->proc->read( heap->data, offs, size, buf );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern void *I3ioReadBuf
             (I3io *i3io,
              int segm,
              Offset offs,
              Size size)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( segm < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( offs < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }

  status = I3ioSet( i3io, segm, &offs, &size );
  if ( pushexception( status ) ) return NULL;

  void *buf = malloc( size ? size : 1 );
  if ( buf == NULL ) {
    pushexception( E_MALLOC ); return NULL;
  }

  Heap *heap = (Heap *)i3io;

  status = heap->proc->read( heap->data, offs, size, buf );
  if ( pushexception( status ) ) { free( buf ); return NULL; }

  return buf;

}


extern void *I3ioReadSegm
             (I3io *i3io,
              int segm,
              Size *size)

{
  Offset off, siz;
  Status status;

  if ( argcheck( i3io == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( segm < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }

  Heap *heap = (Heap *)i3io;

  status = HeapAccess( heap, segm, &off, &siz, NULL );
  if ( pushexception( status ) ) return NULL;

  if ( siz > OffsetMaxSize ) { pushexception( E_I3IO_LEN ); return NULL; }
  if ( size != NULL ) *size = siz;

  void *buf = malloc( siz ? siz : 1 );
  if ( buf == NULL ) {
    pushexception( E_MALLOC ); return NULL;
  }

  status = heap->proc->read( heap->data, off, siz, buf );
  if ( pushexception( status ) ) { free( buf ); return NULL; }

  return buf;

}
