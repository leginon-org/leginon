/*----------------------------------------------------------------------------*
*
*  heapflush.c  -  io: heap management
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
#include <stdlib.h>


/* functions */

extern Status HeapFlush
              (Heap *heap)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  if ( ~heap->mode & IOWr ) {
    return exception( E_HEAP_WR );
  }

  if ( heap->hdr[5] & HeapStatSerr ) {
    return exception( E_HEAP_SYN );
  }

  HeapAtom *hdr = heap->hdr;
  HeapAtom *dir = heap->dir;

  HeapDebugMain( ".flush", "stat", hdr[5] );

  if ( ~heap->stat & HeapStatDbuf ) {

    if ( hdr[5] & HeapStatSync ) {

      status = HeapSync( heap, hdr, dir );
      if ( exception( status ) ) return status;

    } else {

      if ( heap->proc->sync != NULL ) {
        status = heap->proc->sync( heap->data );
        if ( exception( status ) ) return status;
      }

    }

  }

  return E_NONE;

}
