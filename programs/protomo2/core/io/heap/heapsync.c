/*----------------------------------------------------------------------------*
*
*  heapsync.c  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "heapcommon.h"
#include "heapdebug.h"
#include "exception.h"


/* functions */

extern Status HeapHdrSync
              (Heap *heap,
               HeapAtom *hdr,
               HeapAtom stat)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( hdr == NULL ) ) return exception( E_ARGVAL );

  if ( ~heap->mode & IOWr ) {
    return exception( E_HEAP_WR );
  }

  if ( heap->hdr[5] & HeapStatSerr ) {
    return exception( E_HEAP_SYN );
  }

  HeapAtom hdr5 = hdr[5];

  hdr[5] &= ~stat;

  status = HeapWrite( heap, 0, hdr, HeapHdrSize );
  if ( exception( status ) ) goto error;

  if ( heap->proc->sync != NULL ) {
    status = heap->proc->sync( heap->data );
    if ( exception( status ) ) goto error;
  }

  return E_NONE;

  error:
  hdr[5] |= ( hdr5 & stat ) | HeapStatSerr;
  heap->hdr[5] |= HeapStatSerr;

  return status;

}


extern Status HeapSync
              (Heap *heap,
               HeapAtom *hdr,
               HeapAtom *dir)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( hdr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dir == NULL ) ) return exception( E_ARGVAL );

  if ( ~heap->mode & IOWr ) {
    return exception( E_HEAP_WR );
  }

  if ( heap->hdr[5] & HeapStatSerr ) {
    return exception( E_HEAP_SYN );
  }

  HeapDebugComm( "seg.sync", "size", hdr[2] );

  status = HeapDirWrite( heap, hdr, dir );
  if ( exception( status ) ) return status;

  if ( heap->proc->sync != NULL ) {
    status = heap->proc->sync( heap->data );
    if ( exception( status ) ) return status;
  }

  status = HeapHdrSync( heap, hdr, HeapStatSync );
  if ( exception( status ) ) return status;

  return E_NONE;

}
