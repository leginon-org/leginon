/*----------------------------------------------------------------------------*
*
*  heap.c  -  io: heap management
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
#include "baselib.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern void HeapPack
            (Size count,
             const HeapAtom *src,
             void *dst)

{
  unsigned char *d = dst;

  while ( count-- ) {
    HeapAtom atom = *src++;
    for ( Size i = 0; i < sizeof(HeapAtom); i++ ) {
      *d++ = atom; atom >>= 8;
    }
  }

}


extern void HeapUnpack
            (Size count,
             const void *src,
             HeapAtom *dst)

{
  const unsigned char *s = src;

  s += count * sizeof(HeapAtom);
  dst += count;

  while ( count-- ) {
    HeapAtom atom = *--s;
    for ( Size i = 1; i < sizeof(HeapAtom); i++ ) {
       atom <<= 8; atom |= *--s;
    }
    *--dst = atom;
  }

}


extern Status HeapRead
              (Heap *heap,
               HeapAtom offs,
               HeapAtom *dst,
               Size count)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst  == NULL ) ) return exception( E_ARGVAL );

  status = heap->proc->read( heap->data, offs * sizeof(HeapAtom), count * sizeof(HeapAtom), dst );
  if ( exception( status ) ) return status;

  if ( heap->stat & HeapStatPack ) {
    HeapUnpack( count, dst, dst );
  }

  return E_NONE;

}


extern Status HeapWrite
              (Heap *heap,
               HeapAtom offs,
               const HeapAtom *src,
               Size count)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src  == NULL ) ) return exception( E_ARGVAL );

  if ( heap->stat & HeapStatPack ) {

    while ( count ) {

      Size size = count; if ( size > HeapTmpSize ) size = HeapTmpSize;
      HeapPack( size, src, heap->tmp );
      src += size;

      status = heap->proc->write( heap->data, offs * sizeof(HeapAtom), size * sizeof(HeapAtom), heap->tmp );
      if ( exception( status ) ) return status;

      offs += size;
      count -= size;

    }

  } else {

    status = heap->proc->write( heap->data, offs * sizeof(HeapAtom), count * sizeof(HeapAtom), src );
    if ( exception( status ) ) return status;

  }

  return E_NONE;

}


extern Status HeapClear
              (Heap *heap,
               HeapAtom offs,
               HeapAtom size)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  if ( !size ) return E_NONE;

  Size s = ( size < HeapTmpSize ) ? size : HeapTmpSize;
  memset( heap->tmp, 0, s * sizeof(HeapAtom) );

  while ( size ) {

    s = ( size < HeapTmpSize ) ? size : HeapTmpSize;
    status = heap->proc->write( heap->data, offs * sizeof(HeapAtom), s * sizeof(HeapAtom), heap->tmp );
    if ( exception( status ) ) return status;
    offs += s;
    size -= s;

  }

  return E_NONE;

}


extern void HeapMod
            (Heap *heap,
             HeapAtom *hdr)

{

  Time *tm = (Time *)( hdr + 7 );
  *tm = TimeGet();

  hdr[5] |= HeapStatSync;

}


extern void HeapErr
            (Heap *heap,
             HeapAtom *hdr,
             HeapAtom *dir)

{

  if ( dir != heap->dir ) free( dir );

}
