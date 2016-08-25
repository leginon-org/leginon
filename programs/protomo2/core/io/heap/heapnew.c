/*----------------------------------------------------------------------------*
*
*  heapnew.c  -  io: heap management
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
#include <string.h>


/* functions */

extern Status HeapNew
              (Heap *heap,
               Offset size,
               HeapMeta meta,
               int *segm,
               Offset *offs)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( size < 0 ) )     return exception( E_ARGVAL );
  if ( argcheck( segm == NULL ) ) return exception( E_ARGVAL );

  if ( ~heap->mode & IOMod ) {
    return exception( E_HEAP_MOD );
  }

  HeapAtom *hdr = heap->hdr;
  HeapAtom *dir = heap->dir;
  if ( dir == NULL ) return exception( E_HEAP );

  HeapAtom newsize = size; newsize += sizeof(HeapAtom);
  HeapDebugMain( ".new", "size", newsize );

  HeapIndex ent, new; HeapAtom newoffs, newalloc;
  status = HeapSegSearch( dir, HeapDirCount, newsize, &ent, &new, &newoffs, &newalloc );
  if ( exception( status ) ) return status;

  HeapAtom buf[HeapHdrSize];

  if ( new ) {

    if ( ent ) {
      HeapSegSplit( dir, ent, new, newsize, newalloc );
    }

  } else {

    if ( ~heap->mode & IOExt ) {
      return exception( E_HEAP_MOD );
    }

    memcpy( buf, hdr, sizeof(buf) );
    hdr = buf;

    status = HeapDirAlloc( heap, hdr, &dir, &new, 0 );
    if ( exception( status ) ) goto error;

    status = HeapExtend( heap, hdr, dir, newsize, &new, &newoffs, &newalloc );
    if ( exception( status ) ) goto error;

    HeapDebugComm( "seg.alloc", "seg", new );

  }

  DirSize( new ) = newsize;
  DirMeta( new ) = meta;

  status = HeapWrite( heap, newoffs, &newoffs, 1 );
  if ( exception( status ) ) goto error;

  HeapMod( heap, hdr );

  if ( ~heap->mode & IOBuf ) {
    status = HeapSync( heap, hdr, dir );
    if ( exception( status ) ) goto error;
  }

  if ( dir != heap->dir ) {
    free( heap->dir ); heap->dir = dir;
  }
  if ( hdr != heap->hdr ) {
    memcpy( heap->hdr, hdr, HeapHdrSize * sizeof(HeapAtom) );
  }

  *segm = new / HeapEntSize - HeapSegMin;

  if ( offs != NULL ) *offs = ( newoffs + 1 ) * sizeof(HeapAtom);

  return E_NONE;

  error:
  HeapErr( heap, hdr, dir );

  return status;

}
