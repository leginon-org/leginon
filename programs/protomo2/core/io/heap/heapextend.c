/*----------------------------------------------------------------------------*
*
*  heapextend.c  -  io: heap management
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

extern Status HeapExtend
              (Heap *heap,
               HeapAtom *hdr,
               HeapAtom *dir,
               HeapAtom size,
               HeapIndex *seg,
               HeapAtom *offs,
               HeapAtom *allo)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( hdr  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dir  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( size > HeapSegMax ) ) return exception( E_ARGVAL );
  if ( argcheck( offs == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( allo == NULL ) ) return exception( E_ARGVAL );

  if ( hdr[2] != DirOffs( HeapEndInd ) ) return exception( E_HEAP_ERR );

  HeapIndex pre = DirPrev( HeapEndInd );
  HeapIndex ind = DirSize( pre ) ? HeapEndInd : pre;
  *offs = DirOffs( ind );
  *allo = ( size + sizeof(HeapAtom) - 1 ) / sizeof(HeapAtom);
  HeapAtom newsize = *offs + *allo;
  if ( ( newsize < *offs ) || ( newsize > HeapSegMax / sizeof(HeapAtom) ) ) return exception( E_HEAP_SIZE );
  HeapDebugComm( "seg.extend", "size", size );

  if ( newsize > hdr[2] ) {
    status = heap->proc->resize( heap->data, &heap->size, newsize * sizeof(HeapAtom) );
    if ( exception( status ) ) return status;
  }

  if ( seg != NULL ) {
    if ( ind == HeapEndInd ) {
      if ( ( *seg < HeapSegInd ) && ( *seg != HeapDirInd ) ) return exception( E_HEAP );
      SetNext( pre, *seg );
      SetEnt( *seg, pre, HeapEndInd, *offs, 0, 0 );
      SetLink( HeapEndInd, *seg, 0 );
    } else {
      *seg = ind;
    }
    DirOffs( HeapEndInd ) = hdr[2] = newsize;
  }

  return E_NONE;

}
