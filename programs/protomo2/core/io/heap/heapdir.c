/*----------------------------------------------------------------------------*
*
*  heapdir.c  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "heapdebugcommon.h"
#include "exception.h"
#include "message.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status HeapDirCheck
              (const HeapAtom *hdr,
               const HeapAtom *dir,
               HeapAtom *tmp)

{
  Status status;

  if ( dir[0] != HeapDirOffs ) {
    status = exception( E_HEAP_ERR ); goto error;
  }

  status = HeapDirCheckEnt( hdr, dir );
  if ( exception( status ) ) goto error;

  status = HeapDirCheckLinks( hdr, dir, tmp );
  if ( exception( status ) ) goto error;

  return E_NONE;

  error:

  if ( heapdebug ) {
    MessageBegin( "dump(dircheck)", "\n" );
    HeapDebugDump( stderr, hdr, dir );
    MessageEnd( "end(dircheck)", "\n" );
  }

  return status;

}


extern Status HeapDirRead
              (Heap *heap)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  HeapAtom *hdr = heap->hdr;

  HeapAtom *dir = malloc( HeapDirSize * sizeof(HeapAtom) );
  if ( dir == NULL ) return exception( E_MALLOC );

  status = HeapRead( heap, HeapDirOffs, dir, HeapDirSize );
  if ( exception( status ) ) goto error;

  status = HeapDirCheck( hdr, dir, heap->tmp );
  if ( exception( status ) ) goto error;

  if ( !DirLink( HeapDirInd ) ) {
    status = exception( E_HEAP_ERR ); goto error;
  }

  HeapDebugComm( "dir.read", "count", HeapDirCount );

  if ( heap->stat & HeapStatDbuf ) {

    HeapIndex pre = DirPrev( HeapDirInd );
    HeapIndex nxt = DirNext( HeapDirInd );
    SetNext( pre, nxt );
    SetPrev( nxt, pre );
    DirLink( HeapDirInd ) = 0;
    DirOffs( HeapDirInd ) = 0;
    DirSize( HeapDirInd ) = 0;
    HeapDirOffs = dir[0] = 0;

  }

  if ( heap->dir != NULL ) free( heap->dir );
  heap->dir = dir;

  return E_NONE;

  error:
  free( dir );

  return status;

}


extern Status HeapDirWrite
              (Heap *heap,
               const HeapAtom *hdr,
               const HeapAtom *dir)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( hdr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dir == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck ) {
    status = HeapDirCheck( hdr, dir, heap->tmp );
    if ( exception( status ) ) return status;
  }

  HeapDebugComm( "dir.write", "count", HeapDirCount );

  status = HeapWrite( heap, HeapDirOffs, dir, HeapDirSize );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status HeapDirCheckEnt
              (const HeapAtom *hdr,
               const HeapAtom *dir)

{

  if (  DirPrev( HeapHdrInd ) ) return exception( E_HEAP_ERR );
  if ( !DirNext( HeapHdrInd ) ) return exception( E_HEAP_ERR );
  if ( !DirPrev( HeapEndInd ) ) return exception( E_HEAP_ERR );
  if (  DirNext( HeapEndInd ) ) return exception( E_HEAP_ERR );

  if ( DirLink( HeapDirInd ) ) {

    HeapAtom diroffs = DirOffs( HeapDirInd );
    HeapAtom dirsize = DirSize( HeapDirInd );
    if ( diroffs != HeapDirOffs ) return exception( E_HEAP_ERR );
    if ( dirsize != HeapDirSize * sizeof(HeapAtom) ) return exception( E_HEAP_ERR );

    HeapIndex pre = DirPrev( HeapDirInd );
    if ( pre % HeapEntSize ) return exception( E_HEAP_ERR );
    HeapIndex nxt = DirNext( HeapDirInd );
    if ( !nxt || ( nxt % HeapEntSize ) ) return exception( E_HEAP_ERR );
    if (  nxt / HeapEntSize >= HeapDirCount ) return exception( E_HEAP_ERR );
    HeapAtom nxtoffs = DirOffs( nxt );
    if ( diroffs >= nxtoffs ) return exception( E_HEAP_ERR );

    HeapAtom diralloc = nxtoffs - diroffs;
    if ( diralloc < HeapDirSize ) return exception( E_HEAP_ERR );

  }

  return E_NONE;

}


extern Status HeapDirCheckLinks
              (const HeapAtom *hdr,
               const HeapAtom *dir,
               HeapAtom *tmp)

{

  if ( HeapDirCount > HeapTmpSize * sizeof(HeapAtom) ) {
    return exception( E_HEAP );
  }
  uint8_t *ent = (uint8_t *)tmp;
  memset( ent, 0, HeapDirCount );

  HeapAtom dircount = HeapDirCount * HeapEntSize;
  for ( Size i = 0, j = 0; i < dircount; i += HeapEntSize, j++ ) {
    HeapAtom offs = DirOffs( i );
    HeapAtom size = DirSize( i );
    if ( DirLink( i ) ) {
      HeapIndex p = DirPrev( i );
      if ( i == HeapHdrInd ) {
        if ( p ) return exception( E_HEAP_ERR );
      } else {
        if ( ( p % HeapEntSize ) || ( p >= dircount ) ) return exception( E_HEAP_ERR );
        p /= HeapEntSize;
        if ( ent[p] & 1 ) return exception( E_HEAP_ERR );
        ent[p] |= 1;
      }
      HeapIndex n = DirNext( i );
      if ( i == HeapEndInd ) {
        if ( n ) return exception( E_HEAP_ERR );
        if ( offs != hdr[2] ) return exception( E_HEAP_ERR );
        if ( size ) return exception( E_HEAP_ERR );
      } else {
        if ( ( n % HeapEntSize ) || ( n >= dircount ) ) return exception( E_HEAP_ERR );
        n /= HeapEntSize;
        if ( ent[n] & 2 ) return exception( E_HEAP_ERR );
        ent[n] |= 2;
        if ( offs >= hdr[2] ) return exception( E_HEAP_ERR );
        size = ( size + sizeof(HeapAtom) - 1 ) / sizeof(HeapAtom);
        offs += size;
        if ( ( offs < size ) || ( offs > hdr[2] ) ) return exception( E_HEAP_ERR );
      }
      ent[j] |= 4;
    } else {
      if ( offs ) return exception( E_HEAP_ERR );
      if ( size ) return exception( E_HEAP_ERR );
    }
  }

  HeapAtom sizenum = 0, sizemin = HeapSegMax, sizemax = 0, sizetot = 0;
  HeapAtom allonum = 0, allomin = HeapSegMax, allomax = 0, allotot = 0;
  HeapAtom freenum = 0, freemin = HeapSegMax, freemax = 0, freetot = 0;
  Bool first = True;

  HeapAtom offs = DirOffs( HeapHdrInd );
  HeapAtom size = DirSize( HeapHdrInd );
  HeapIndex ind = DirNext( HeapHdrInd );
  do {
    HeapAtom off = DirOffs( ind );
    if ( off <= offs ) return exception( E_HEAP_ERR );
    if ( !first ) {
      HeapAtom alloc = off - offs;
      if ( size ) {
        sizenum++;
        if ( size < sizemin ) sizemin = size;
        if ( size > sizemax ) sizemax = size;
        sizetot += size;
        allonum++;
        if ( alloc < allomin ) allomin = alloc;
        if ( alloc > allomax ) allomax = alloc;
        allotot += alloc;
      } else {
        freenum++;
        if ( alloc < freemin ) freemin = alloc;
        if ( alloc > freemax ) freemax = alloc;
        freetot += alloc;
      }
    }
    if ( size && ( size < sizeof(HeapAtom) ) ) return exception( E_HEAP_ERR );
    size = ( size + sizeof(HeapAtom) - 1 ) / sizeof(HeapAtom);
    offs += size; if ( offs < size ) return exception( E_HEAP_ERR );
    if ( off < offs ) return exception( E_HEAP_ERR );
    offs = off;
    size = DirSize( ind );
    ent[ind/HeapEntSize] = 0;
    ind = DirNext( ind );
    first = False;
  } while ( ind );

  for ( Size i = 0, j = 0; i < dircount; i += HeapEntSize, j++ ) {
    if ( ent[j] && ( i != HeapHdrInd ) && ( i == HeapEndInd ) ) return exception( E_HEAP_ERR );
  }

  if ( sizenum ) {
    sizemin -= sizeof(HeapAtom);
    sizemax -= sizeof(HeapAtom);
    sizetot -= sizenum * sizeof(HeapAtom);
  } else {
    sizemin = 0;
  }
  if ( !allonum ) allomin = 0;
  if ( !freenum ) freemin = 0;
  tmp[0] = sizenum; tmp[1] = sizemin; tmp[2]  = sizemax; tmp[3]  = sizetot;
  tmp[4] = allonum; tmp[5] = allomin; tmp[6]  = allomax; tmp[7]  = allotot;
  tmp[8] = freenum; tmp[9] = freemin; tmp[10] = freemax; tmp[11] = freetot;

  return E_NONE;

}


extern Status HeapDirAlloc
              (Heap *heap,
               HeapAtom *hdr,
               HeapAtom **ptr,
               HeapIndex *seg,
               HeapIndex ind)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( hdr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( ptr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( seg == NULL ) ) return exception( E_ARGVAL );

  HeapAtom *dir = *ptr;

  if ( runcheck ) {
    status = HeapDirCheck( hdr, dir, heap->tmp );
    if ( exception( status ) ) return status;
  }

  HeapIndex dircurr, dirhigh;
  HeapIndex dirnext = HeapDirCount * HeapEntSize;
  HeapIndex ent = dirnext, idx = ent + HeapEntSize, spl = 0;

  if ( ind < dirnext ) {
    dirhigh = dirnext;
    dircurr = dirnext + HeapEntInc * HeapEntSize;
    if ( !(ind < HeapSegInd ) ) {
      if ( DirSize( ind ) ) return exception( E_HEAP_EXIST );
    }
  } else {
    dirhigh = ind + HeapEntSize;
    dircurr = dirnext + 3 * HeapEntSize;
    if ( ind == dirnext ) {
      ent += HeapEntSize; idx += HeapEntSize;
    } else if ( ind == dirnext + HeapEntSize ) {
      idx += HeapEntSize;
    }
  }

  HeapIndex i = HeapSegInd;
  while ( ( i < dirnext ) && ( DirLink( i ) || ( i == ind ) ) ) i += HeapEntSize;
  if ( i < dirnext ) {
    idx = i; dircurr -= HeapEntSize;
    do i += HeapEntSize; while ( ( i < dirnext ) && ( DirLink( i ) || ( i == ind ) ) );
    if ( i < dirnext ) {
      ent = i; dircurr -= HeapEntSize;
      do i += HeapEntSize; while ( ( i < dirnext ) && ( DirLink( i ) || ( i == ind ) ) );
      if ( i < dirnext ) {
        spl = i; dircurr = dirhigh;
      }
    }
  }
  if ( dircurr < dirhigh ) dircurr = dirhigh;
  if ( heap->stat & HeapStatDbuf ) {
    if ( idx < dirnext ) {
      dircurr = dirhigh;
      if ( ent >= dirnext ) dircurr += HeapEntSize;
    }
  }

  HeapIndex inclen = dircurr - dirnext;
  HeapIndex dirinc = inclen / HeapEntSize;

  HeapAtom dirlen = HeapDirSize, dirsize = dirlen * sizeof(HeapAtom);
  HeapAtom newlen = dirlen + inclen;
  if ( ( newlen < dirlen ) || ( newlen >= HeapEntMax ) ) {
    return exception( E_HEAP_DIR );
  }
  HeapAtom newsize = newlen * sizeof(HeapAtom);

  if ( newsize > dirsize ) {
    dir = malloc( newsize );
    if ( dir == NULL ) return exception( E_MALLOC );
    memcpy( dir, *ptr, dirsize );
    memset( dir + dirlen, 0, inclen * sizeof(HeapAtom) );
  }

  HeapSegMerge( dir );

  HeapAtom newalloc, newoffs = 0;
  HeapIndex new = 0;

  if ( ( ~heap->stat & HeapStatDbuf ) || ( ~heap->mode & IOExt ) ) {
    status = HeapSegSearch( dir, HeapDirCount, newsize, NULL, &new, &newoffs, &newalloc );
    if ( exception( status ) ) goto error;
  }

  if ( !new ) {

    if ( ~heap->mode & IOExt ) {
      status = exception( E_HEAP_MOD ); goto error;
    }

    if ( heap->stat & HeapStatDbuf ) {

      HeapAtom len = heap->size / sizeof(HeapAtom);
      len = ( len > hdr[2] ) ? len - hdr[2] : 0;
      newlen = ( newlen > len ) ? newlen - len : 0;
      newsize = newlen * sizeof(HeapAtom);
      status = HeapExtend( heap, hdr, dir, newsize, NULL, &newoffs, &newalloc );
      if ( exception( status ) ) goto error;

    } else {

      new = ent; spl = 0;
      status = HeapExtend( heap, hdr, dir, newsize, &new, &newoffs, &newalloc );
      if ( exception( status ) ) goto error;

    }

  }

  if ( ~heap->stat & HeapStatDbuf ) {
    HeapDebugComm( "dir.swap", "seg", new );
    HeapSegSwap( dir, HeapDirInd, new, newsize, 0 ); 
    if ( spl ) {
      HeapDebugComm( "dir.split", "seg", spl );
      HeapSegSplit( dir, spl, HeapDirInd, newsize, newalloc );
    }
  }

  HeapDirOffs = dir[0] = newoffs;
  HeapDirCount += dirinc;

  HeapDebugComm( "dir.alloc", "seg", ind );

  *ptr = dir;
  *seg = idx;

  return E_NONE;

  error:

  if ( heapdebug ) {
    MessageBegin( "dump(diralloc)", "\n" );
    HeapDebugDump( stderr, hdr, dir );
    MessageEnd( "end(diralloc)", "\n" );
  }

  free( dir );

  return status;

}
