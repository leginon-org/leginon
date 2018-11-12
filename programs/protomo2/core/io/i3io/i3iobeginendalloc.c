/*----------------------------------------------------------------------------*
*
*  i3iobeginendalloc.c  -  io: i3 input/output
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

extern void *I3ioBeginWriteAlloc
             (I3io *i3io,
              int segm,
              Size size,
              I3ioMeta meta)

{
  Offset offs;
  void *addr;
  Status status;

  if ( argcheck( i3io == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( segm < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }

  Heap *heap = (Heap *)i3io;

  status = HeapAlloc( heap, segm, size, meta, &offs );
  if ( pushexception( status ) ) return NULL;

  if ( heap->proc->addr == NULL ) {

    addr = malloc( size ? size : 1 );
    if ( addr == NULL ) {
      pushexception( E_MALLOC ); goto error;
    }

  } else {

    status = heap->proc->addr( heap->data, offs, size, &addr );
    if ( pushexception( status ) ) goto error;

  }

  return addr;

  error:

  status = HeapDealloc( heap, segm );
  logexception( status );

  return NULL;

}


extern Status I3ioEndWriteAlloc
              (I3io *i3io,
               int segm,
               Size size,
               void *addr,
               Status fail)

{
  Offset offs = 0;
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );

  Heap *heap = (Heap *)i3io;

  status = I3ioSet( i3io, segm, &offs, &size );
  if ( exception( status ) ) goto error;

  if ( heap->proc->addr == NULL ) {

    if ( !fail ) {

      if ( addr == NULL ) {
        return exception( E_I3IO );
      }

      status = heap->proc->write( heap->data, offs, size, addr );
      if ( exception( status ) ) goto error;

    }

    if ( addr != NULL ) free( addr );

  }

  if ( fail ) goto error;

  return E_NONE;

  error:

  fail = HeapDealloc( heap, segm );
  logexception( fail );

  return status;

}
