/*----------------------------------------------------------------------------*
*
*  heapdealloc.c  -  io: heap management
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

extern Status HeapDealloc
              (Heap *heap,
               int segm)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  if ( ~heap->mode & IOMod ) {
    return exception( E_HEAP_MOD );
  }

  HeapAtom *hdr = heap->hdr;
  HeapAtom *dir = heap->dir;
  if ( dir == NULL ) return exception( E_HEAP );

  if ( segm < 0 ) return exception( E_ARGVAL );
  if ( (Size)segm >= HeapSegCount ) return exception( E_HEAP_SEGM );

  HeapIndex seg = ( segm + HeapSegMin ) * HeapEntSize;
  if ( !DirSize( seg ) ) return exception( E_HEAP_SEGM );
  HeapDebugMain( ".dealloc", "seg", seg );

  if ( !DirLink( seg ) ) return exception( E_HEAP );
  HeapIndex nxt = DirNext( seg );

  HeapAtom segoffs = DirOffs( seg ), nxtoffs = DirOffs( nxt );
  if ( segoffs >= nxtoffs ) return exception( E_HEAP_ERR );
  HeapAtom segalloc = nxtoffs - segoffs;

  DirSize( seg ) = 0;
  DirMeta( seg ) = 0;

  HeapMod( heap, hdr );

  if ( ~heap->mode & IOBuf ) {
    status = HeapDirWrite( heap, hdr, dir );
    if ( exception( status ) ) return status;
  }

  status = HeapClear( heap, segoffs, segalloc );
  if ( exception( status ) ) return status;

  return E_NONE;

}
