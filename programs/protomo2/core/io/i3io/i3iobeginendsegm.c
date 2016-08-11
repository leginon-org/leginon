/*----------------------------------------------------------------------------*
*
*  i3iobeginendsegm.c  -  io: i3 input/output
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

extern void *I3ioBeginReadSegm
             (I3io *i3io,
              int segm,
              Size *size)

{
  Offset off, siz;
  void *addr;
  Status status;

  if ( argcheck( i3io == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( segm < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }

  Heap *heap = (Heap *)i3io;

  status = HeapAccess( heap, segm, &off, &siz, NULL );
  if ( pushexception( status ) ) return NULL;

  if ( siz > OffsetMaxSize ) { pushexception( E_I3IO_LEN ); return NULL; }
  if ( size != NULL ) *size = siz;

  if ( heap->proc->addr == NULL ) {

    addr = malloc( siz ? siz : 1 );
    if ( addr == NULL ) {
      pushexception( E_MALLOC ); return NULL;
    }

    status = heap->proc->read( heap->data, off, siz, addr );
    if ( pushexception( status ) ) {
      free( addr ); return NULL;
    }

  } else {

    status = heap->proc->addr( heap->data, off, siz, &addr );
    if ( pushexception( status ) ) return NULL;

  }

  return addr;

}


extern void *I3ioBeginWriteSegm
             (I3io *i3io,
              int segm,
              Size *size)

{
  Offset off, siz;
  void *addr;
  Status status;

  if ( argcheck( i3io == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( segm < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }

  Heap *heap = (Heap *)i3io;

  status = HeapAccess( heap, segm, &off, &siz, NULL );
  if ( pushexception( status ) ) return NULL;

  if ( siz > OffsetMaxSize ) { pushexception( E_I3IO_LEN ); return NULL; }
  if ( size != NULL ) *size = siz;

  if ( heap->proc->addr == NULL ) {

    addr = malloc( siz ? siz : 1 );
    if ( addr == NULL ) {
      pushexception( E_MALLOC ); return NULL;
    }

  } else {

    status = heap->proc->addr( heap->data, off, siz, &addr );
    if ( pushexception( status ) ) return NULL;

  }

  return addr;

}


extern Status I3ioEndReadSegm
              (I3io *i3io,
               int segm,
               void *addr)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );

  Heap *heap = (Heap *)i3io;

  status = HeapAccess( heap, segm, NULL, NULL, NULL );
  if ( exception( status ) ) return status;

  if ( heap->proc->addr == NULL ) {

    if ( addr == NULL ) {
      return exception( E_I3IO );
    }
    free( addr );

  }

  return E_NONE;

}


extern Status I3ioEndWriteSegm
              (I3io *i3io,
               int segm,
               void *addr)

{
  Offset off, siz;
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );

  Heap *heap = (Heap *)i3io;

  status = HeapAccess( heap, segm, &off, &siz, NULL );
  if ( exception( status ) ) return status;

  if ( heap->proc->addr == NULL ) {

    if ( addr == NULL ) {
      return exception( E_I3IO );
    }

    status = heap->proc->write( heap->data, off, siz, addr );
    if ( exception( status ) ) return status;

    free( addr );

  }

  return E_NONE;

}
