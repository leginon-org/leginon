/*----------------------------------------------------------------------------*
*
*  heapresize.c  -  io: heap management
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

static Status HeapSegMove
              (Heap *heap,
               HeapAtom srcoffs,
               HeapAtom srcsize,
               HeapAtom dstoffs,
               HeapAtom dstsize)

{
  HeapAtom offs;
  Status status;

  if ( dstsize < srcsize ) return exception( E_ARGVAL );

  if ( !srcsize ) return exception( E_HEAP );
  status = HeapRead( heap, srcoffs, &offs, 1 );
  if ( exception( status ) ) return status;
  if ( offs != srcoffs ) return exception( E_HEAP_ERR );
  HeapAtom *tmp = heap->tmp;

  while ( srcsize ) {

    Size size = ( srcsize < HeapTmpSize ) ? srcsize : HeapTmpSize;
    status = heap->proc->read( heap->data, srcoffs * sizeof(HeapAtom), size * sizeof(HeapAtom), tmp );
    if ( exception( status ) ) return status;
    srcoffs += size;
    srcsize -= size;

    if ( offs ) tmp[0] = offs = 0;

    status = heap->proc->write( heap->data, dstoffs * sizeof(HeapAtom), size * sizeof(HeapAtom), tmp );
    if ( exception( status ) ) return status;
    dstoffs += size;
    dstsize -= size;

  }

  if ( dstsize ) {

    memset( tmp, 0, HeapTmpSize * sizeof(HeapAtom) );

    while ( dstsize ) {

      Size size = ( dstsize < HeapTmpSize ) ? dstsize : HeapTmpSize;
      status = heap->proc->write( heap->data, dstoffs * sizeof(HeapAtom), size * sizeof(HeapAtom), tmp );
      if ( exception( status ) ) return status;
      dstoffs += size;
      dstsize -= size;

    }

  }

  return E_NONE;

}


extern Status HeapResize
              (Heap *heap,
               int segm,
               Offset size,
               Offset *offs)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( size < 0 ) ) return exception( E_ARGVAL );

  if ( ~heap->mode & IOWr ) {
    return exception( E_HEAP_WR );
  }

  HeapAtom *hdr = heap->hdr;
  HeapAtom *dir = heap->dir;
  if ( dir == NULL ) return exception( E_HEAP );

  if ( segm < 0 ) return exception( E_ARGVAL );
  if ( (Size)segm >= HeapSegCount ) return exception( E_HEAP_SEGM );

  HeapIndex seg = ( segm + HeapSegMin ) * HeapEntSize;
  if ( !DirSize( seg ) ) return exception( E_HEAP_SEGM );
  HeapDebugMain( ".resize", "seg", seg );

  if ( !DirLink( seg ) ) return exception( E_HEAP );
  HeapIndex nxt = DirNext( seg );

  HeapAtom segoffs = DirOffs( seg ), nxtoffs = DirOffs( nxt );
  if ( segoffs >= nxtoffs ) return exception( E_HEAP_ERR );
  HeapAtom segalloc = ( nxtoffs - segoffs ) * sizeof(HeapAtom);

  HeapAtom segsize = DirSize( seg );
  if ( segsize < sizeof(HeapAtom) ) return exception( E_HEAP_ERR );
  if ( segsize > segalloc ) return exception( E_HEAP_ERR );
  HeapAtom segmeta = DirMeta( seg );

  HeapAtom buf[HeapHdrSize];

  HeapAtom newsize = size; newsize += sizeof(HeapAtom);
  HeapDebugMain( ".resize", "size", newsize );

  if ( newsize <= segalloc ) {

    DirSize( seg ) = newsize;

    HeapMod( heap, hdr );

    if ( ~heap->mode & IOBuf ) {
      status = HeapDirWrite( heap, hdr, dir );
      if ( exception( status ) ) return status;
    }

  } else {

    if ( ~heap->mode & IOMod ) {
      return exception( E_HEAP_MOD );
    }

    HeapIndex ent, new; HeapAtom newoffs, newalloc;
    status = HeapSegSearch( dir, HeapDirCount, newsize, &ent, &new, &newoffs, &newalloc );
    if ( exception( status ) ) return status;

    if ( !new ) {

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

      ent = 0;

    }

    segsize = ( segsize + sizeof(HeapAtom) - 1 ) / sizeof(HeapAtom);
    status = HeapSegMove( heap, segoffs, segsize, newoffs, newalloc );
    if ( exception( status ) ) goto error;

    status = HeapWrite( heap, newoffs, &newoffs, 1 );
    if ( exception( status ) ) goto error;

    HeapSegSwap( dir, seg, new, newsize, segmeta );

    if ( ent ) {
      HeapSegSplit( dir, ent, seg, newsize, newalloc );
    }

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

    segoffs = newoffs;

  }

  if ( offs != NULL ) *offs = ( segoffs + 1 ) * sizeof(HeapAtom);

  return E_NONE;

  error:
  HeapErr( heap, hdr, dir );

  return status;

}
