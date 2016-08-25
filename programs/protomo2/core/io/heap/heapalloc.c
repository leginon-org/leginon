/*----------------------------------------------------------------------------*
*
*  heapalloc.c  -  io: heap management
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

extern Status HeapAlloc
              (Heap *heap,
               int segm,
               Offset size,
               HeapMeta meta,
               Offset *offs)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( size < 0 ) ) return exception( E_ARGVAL );

  if ( ~heap->mode & IOMod ) {
    return exception( E_HEAP_MOD );
  }

  HeapAtom *hdr = heap->hdr;
  HeapAtom *dir = heap->dir;
  if ( dir == NULL ) return exception( E_HEAP );

  if ( segm < 0 ) return exception( E_ARGVAL );

  HeapIndex seg = ( segm + HeapSegMin ) * HeapEntSize, ind = 0;
  if ( seg < HeapDirCount * HeapEntSize ) {
    if ( DirSize( seg ) ) return exception( E_HEAP_EXIST );
    if ( DirLink( seg ) ) ind = seg;
  }

  HeapDebugMain( ".alloc", "seg", seg );

  HeapIndex ent, new; HeapAtom newoffs, newalloc;
  HeapAtom newsize = size; newsize += sizeof(HeapAtom);
  HeapDebugMain( ".alloc", "size", newsize );

  HeapAtom buf[HeapHdrSize];

  status = HeapSegSearch( dir, HeapDirCount, newsize, &ent, &new, &newoffs, &newalloc );
  if ( exception( status ) ) goto error;

  if ( !new || !( seg < HeapDirCount * HeapEntSize ) ) {

    if ( ~heap->mode & IOExt ) {
      status = exception( E_HEAP_MOD ); goto error;
    }

    memcpy( buf, hdr, sizeof(buf) );
    hdr = buf;

    if ( !ent || !( seg < HeapDirCount * HeapEntSize ) ) {
      status = HeapDirAlloc( heap, hdr, &dir, &ent, seg );
      if ( exception( status ) ) return status;
    }
    new = ent;
    status = HeapExtend( heap, hdr, dir, newsize, &new, &newoffs, &newalloc );
    if ( exception( status ) ) goto error;

    HeapDebugComm( "seg.alloc", "seg", new );

  }

  if ( new == seg ) {
    DirSize( seg ) = newsize;
    DirMeta( seg ) = meta;
  } else if ( ind == seg ) {
    HeapSegSwap( dir, seg, new, newsize, meta );
  } else {
    HeapIndex pre = DirPrev( new ), nex = DirNext( new );
    ClrEnt( new );
    SetEnt( seg, pre, nex, newoffs, newsize, meta );
    SetNext( pre, seg );
    SetPrev( nex, seg );
  }

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

  if ( offs != NULL ) *offs = ( newoffs + 1 ) * sizeof(HeapAtom);

  return E_NONE;

  error:
  HeapErr( heap, hdr, dir );

  return status;

}
