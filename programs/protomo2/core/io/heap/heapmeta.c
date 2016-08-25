/*----------------------------------------------------------------------------*
*
*  heapmeta.c  -  io: heap management
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
#include "exception.h"


/* functions */

extern Status HeapMetaSet
              (Heap *heap,
               int index,
               HeapMeta meta)

{

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  if ( ( index < 0 ) || ( index >= HeapHdrSize - HeapMetaMin ) ) {
    return exception( E_ARGVAL );
  }

  if ( ~heap->mode & IOWr ) {
    return exception( E_HEAP_WR );
  }

  heap->hdr[ HeapMetaMin + index ] = meta;

  HeapMod( heap, heap->hdr );

  return E_NONE;

}


extern Status HeapMetaGet
              (Heap *heap,
               int index,
               HeapMeta *meta)

{

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( meta == NULL ) ) return exception( E_ARGVAL );

  if ( ( index < 0 ) || ( index >= HeapHdrSize - HeapMetaMin ) ) {
    return exception( E_ARGVAL );
  }

  *meta = heap->hdr[ HeapMetaMin + index ];

  return E_NONE;

}
