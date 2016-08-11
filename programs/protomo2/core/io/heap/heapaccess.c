/*----------------------------------------------------------------------------*
*
*  heapaccess.c  -  io: heap management
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

extern Status HeapAccess
               (Heap *heap,
                int segm,
                Offset *offs,
                Offset *size,
                HeapMeta *meta)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  HeapAtom *hdr = heap->hdr;
  HeapAtom *dir = heap->dir;
  if ( dir == NULL ) return exception( E_HEAP );

  if ( segm < 0 ) return exception( E_ARGVAL );
  if ( (Size)segm >= HeapSegCount ) return exception( E_HEAP_SEGM );

  HeapIndex seg = ( segm + HeapSegMin ) * HeapEntSize;
  if ( !DirSize( seg ) ) return exception( E_HEAP_SEGM );
  HeapDebugMain( ".access", "seg", seg );

  if ( !DirLink( seg ) ) return exception( E_HEAP );
  HeapIndex nxt = DirNext( seg );

  HeapAtom segoffs = DirOffs( seg ), nxtoffs = DirOffs( nxt );
  if ( segoffs >= nxtoffs ) return exception( E_HEAP_ERR );
  HeapAtom segalloc = ( nxtoffs - segoffs ) * sizeof(HeapAtom);

  HeapAtom segsize = DirSize( seg );
  if ( segsize < sizeof(HeapAtom) ) return exception( E_HEAP_ERR );
  if ( segsize > segalloc ) return exception( E_HEAP_ERR );

  status = HeapRead( heap, segoffs, &nxtoffs, 1 );
  if ( exception( status ) ) return status;
  if ( segoffs != nxtoffs ) return exception( E_HEAP_ERR );

  if ( offs != NULL ) *offs = ( segoffs + 1 ) * sizeof(HeapAtom);
  if ( size != NULL ) *size = segsize - sizeof(HeapAtom);
  if ( meta != NULL ) *meta = DirMeta( seg );

  return E_NONE;

}
