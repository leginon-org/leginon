/*----------------------------------------------------------------------------*
*
*  heapinit.c  -  io: heap management
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
#include "baselib.h"
#include "exception.h"
#include "macros.h"
#include <stdlib.h>
#include <string.h>


/* variables */

static const union {
  uint8_t  i8[8];
  uint16_t i16[4];
  uint32_t i32[2];
  uint64_t i64[1];
} magic = {
 .i8[0] = 'I',
 .i8[1] = '3',
 .i8[2] = 'D',
 .i8[3] = '-',
 .i8[4] = HeapVersionMajor,
 .i8[5] = HeapVersionMinor,
 .i8[6] = 'L',
 .i8[7] = 'B',
};


/* functions */

static void HeapHdrInit
            (HeapAtom hdr[])

{
  uint8_t m3 = magic.i16[3];

  hdr[0] = m3;
  hdr[0] <<= 8; hdr[0] |= magic.i8[5];
  hdr[0] <<= 8; hdr[0] |= magic.i8[4];
  hdr[0] <<= 8; hdr[0] |= magic.i8[3];
  hdr[0] <<= 8; hdr[0] |= magic.i8[2];
  hdr[0] <<= 8; hdr[0] |= magic.i8[1];
  hdr[0] <<= 8; hdr[0] |= magic.i8[0];

  const char *ident = HeapVers;
  const char *i = ident + strlen( ident );
  char sep = 10;

  hdr[1] = 15;
  while ( i-- > ident ) {
    hdr[1] <<= 4;
    char c = *i;
    if ( ( c >= '0' ) && ( c <= '9' ) ) {
      c -= '0';
    } else if ( c == '.' ) {
      c = sep++; if ( sep >= 14 ) sep = 10;
    } else {
      c = 14;
    }
    hdr[1] |= c;
  }

  hdr[2] = 0;
  hdr[3] = 0;
  hdr[4] = 0;

  hdr[5] = ( ( m3 == 'B' ) ? HeapStatBigE : 0 );

  Time *tm = (Time *)( hdr + 6 );
  *tm = TimeGet();
  hdr[7] = 0;

  for ( Size i = HeapMetaMin; i < HeapHdrSize; i++ ) {
    hdr[i] = 0;
  }

}


static Status HeapHdrCheck
              (HeapAtom *hdr)

{
  HeapAtom atom = hdr[0];

  for ( Size i = 0; i < 5; i++ ) {
    if ( ((uint8_t)atom) != magic.i8[i] ) return E_HEAP_FMT;
    atom >>= 8;
  }
  if ( ((uint8_t)atom) > HeapVersionMinor ) return E_HEAP_INIT;
  atom >>= 8;
  switch ( (uint8_t)atom ) {
    case 'B': hdr[5] |=  HeapStatBigE; break;
    case 'L': hdr[5] &= ~HeapStatBigE; break;
    default: return E_HEAP_INIT;
  }

  if ( HeapDirOffs >= hdr[2] ) return E_HEAP_INIT;
  if ( HeapDirCount > HeapEntMax ) return E_HEAP_INIT;
  if ( HeapDirOffs + HeapDirSize > hdr[2] ) return E_HEAP_INIT;

  return E_NONE;

}


static Status HeapSetPack
              (const HeapAtom *hdr,
               HeapStat *stat)

{

  *stat &= ~HeapStatPack;

  switch ( (uint8_t)magic.i16[3] ) {
    case 'B': if ( !( hdr[5] & HeapStatBigE ) ) *stat |= HeapStatPack; break;
    case 'L': if (  ( hdr[5] & HeapStatBigE ) ) *stat |= HeapStatPack; break;
    default: return exception( E_HEAP );
  }

  return E_NONE;

}


extern HeapMeta *HeapFormat
                 (void *buf,
                  Size len)

{
  HeapAtom *hdr = buf;
  HeapStat stat;
  Status status;

  if ( hdr == NULL ) {
    logexception( E_HEAP ); return NULL;
  }

  if ( len < HeapHdrSize * sizeof(HeapAtom) ) {
    logexception( E_HEAP ); return NULL;
  }

  status = HeapHdrCheck( hdr );
  if ( exception( status ) ) return NULL;

  status = HeapSetPack( hdr, &stat );
  if ( exception( status ) ) return NULL;

  hdr += HeapMetaMin;

  if ( stat & HeapStatPack ) {
    HeapUnpack( HeapHdrSize - HeapMetaMin, hdr, hdr );
  }

  return hdr;

}


static void HeapDirInit
            (HeapAtom *hdr,
             HeapAtom *dir,
             HeapIndex dircount,
             HeapIndex segsize,
             HeapStat stat)

{
  HeapIndex cur, pre = 0;
  HeapAtom size, offs = 0;
  HeapAtom diroffs = 0;

  cur = HeapHdrInd; size = HeapHdrSize;
  SetEnt( cur, pre, 0, offs, size * sizeof(HeapAtom), 0 ); pre = cur; offs += size;

  size = dircount * HeapEntSize + 1;

  if ( stat & HeapStatDbuf ) {

    ClrEnt( HeapDirInd );
    segsize += size;

  } else {

    diroffs = offs;

    cur = HeapDirInd;
    SetNext( pre, cur );
    SetEnt( cur, pre, 0, offs, size * sizeof(HeapAtom), 0 ); pre = cur; offs += size;

  }

  if ( segsize ) {

    cur = HeapSegInd; size = segsize;
    SetNext( pre, cur );
    SetEnt( cur, pre, 0, offs, 0, 0 ); pre = cur; offs += size;

  }

  cur = HeapEndInd;
  SetNext( pre, cur );
  SetEnt( cur, pre, 0, offs, 0, 0 );

  HeapDirOffs = dir[0] = diroffs;
  HeapDirCount = dircount;

  hdr[2] = offs;

}


static Status HeapInitNew
              (Heap *heap,
               Size initsegm,
               Offset initsize)

{
  Status status;

  HeapAtom *hdr = heap->hdr;
  HeapAtom *tmp = heap->tmp;
  HeapAtom *dir;

  HeapAtom dircount = HeapSegMin + MAX( initsegm, 5 );
  HeapAtom dirsize = dircount * HeapEntSize + 1;
  HeapAtom segsize = ( initsize > 0 ) ? initsize / sizeof(HeapAtom) : 0;
  HeapAtom heapsize = HeapHdrSize + dirsize + segsize;

  HeapHdrInit( hdr );

  hdr[5] |= HeapStatOpen;

  memcpy( tmp, hdr, HeapHdrSize * sizeof(HeapAtom) );
  dir = tmp + HeapHdrSize;

  HeapDirInit( tmp, dir, HeapSegMin, 0, 0 );

  status = heap->proc->resize( heap->data, &heap->size, heapsize * sizeof(HeapAtom) );
  if ( exception( status ) ) return status;

  status = HeapWrite( heap, 0, tmp, tmp[2] );
  if ( exception( status ) ) return status;

  if ( heap->proc->sync != NULL ) {
    status = heap->proc->sync( heap->data );
    if ( exception( status ) ) return status;
  }

  dir = malloc( dirsize * sizeof(HeapAtom) );
  if ( dir == NULL ) return exception( E_MALLOC );
  memset( dir, 0, dirsize * sizeof(HeapAtom) );
  heap->dir = dir;

  HeapDirInit( hdr, dir, dircount, segsize, heap->stat );

  hdr[5] |= HeapStatSync;

  return E_NONE;

}


static Status HeapInitOld
              (Heap *heap)

{
  Status status;

  HeapAtom *hdr = heap->hdr;

  status = HeapRead( heap, 0, hdr, HeapHdrSize );
  if ( exception( status ) ) return exception( E_HEAP_INIT );

  status = HeapHdrCheck( hdr );
  if ( exception( status ) ) return status;

  if ( ~heap->mode & IOModeErr ) {
    if ( hdr[5] & HeapStatOpen ) {
      if ( heap->mode & IONew ) return exception( E_HEAP_META );
      if ( heap->mode & IOShr ) return exception( E_HEAP_USE );
      hdr[5] &= ~HeapStatOpen;
    }
    if ( hdr[5] & HeapStatSync ) return exception( E_HEAP_META );
    if ( hdr[5] & HeapStatSerr ) return exception( E_HEAP_META );
  }
  if ( hdr[5] & ( HeapStatOpen | HeapStatSync | HeapStatSerr ) ) {
    heap->mode = IORd;
  }

  status = HeapDirRead( heap );
  if ( exception( status ) ) return exception( E_HEAP_INIT );

  hdr[5] |= HeapStatOpen;

  if ( heap->mode & IOWr ) {

    status = HeapWrite( heap, 0, hdr, HeapHdrSize );
    if ( exception( status ) ) return exception( E_HEAP_INIT );

  }

  return E_NONE;

}


extern Heap *HeapInit
             (const HeapProc *proc,
              void *data,
              const HeapParam *param)

{
  static Size count = 0;
  Status status;

  if ( sizeof(HeapMeta) > sizeof(HeapAtom) ) {
    pushexception( E_HEAP ); goto error0;
  }

  Heap *heap = malloc( sizeof(Heap) );
  if ( heap == NULL ) {
    pushexception( E_MALLOC ); goto error0;
  }

  heap->data = data;
  heap->proc = proc;
  heap->mode = ( param == NULL ) ? ( IOOld | IORd ) : param->mode;
  heap->stat = 0;
  heap->dir  = NULL;
  heap->size = 0;
  heap->nestcount = 0;
  heap->objcount = count++;

  if ( heap->mode & ( IONew | IOCre ) ) heap->mode |= IONew | IOCre | IOExt;
  if ( heap->mode & IOExt ) heap->mode |= IOMod;
  if ( heap->mode & IOMod ) heap->mode |= IOWr;
  if ( heap->mode & IOShr ) heap->mode &= ~IOBuf;

  if ( ( heap->mode & IOExt ) && ( heap->mode & IOBuf ) ) {
    heap->stat = HeapStatDbuf;
  }

  if ( ( heap->proc == NULL )
    || ( heap->proc->read == NULL )   || ( heap->proc->write == NULL )
    || ( heap->proc->resize == NULL ) || ( heap->proc->final == NULL ) ) {
    pushexception( E_HEAP ); goto error1;
  }

  if ( proc->init != NULL ) {
    status = proc->init( heap->data );
    if ( pushexception( status ) ) goto error1;
  }

  data = NULL;

  if ( heap->mode & IOShr ) {
    if ( ( heap->proc->lock == NULL ) || ( heap->proc->unlock == NULL ) ) {
      pushexception( E_HEAP ); goto error2;
    }
    status = heap->proc->lock( heap->data, 0, 1 );
    if ( pushexception( status ) ) goto error2;
  }

  if ( heap->mode & ( IONew | IOCre ) ) {

    Size initsegm = ( param == NULL ) ? 0 : param->initsegm;
    Offset initsize = ( param == NULL ) ? 0 : param->initsize;
    HeapDebugMain( ".init", "new", initsize );

    status = HeapInitNew( heap, initsegm, initsize );
    if ( pushexception( status ) ) goto error3;

  } else if ( heap->mode & IORd ) {

    HeapDebugMain( ".init", "old", 0 );

    status = HeapInitOld( heap );
    if ( pushexception( status ) ) goto error3;

  } else {

    status = pushexception( E_HEAP ); goto error3;

  }

  status = HeapSetPack( heap->hdr, &heap->stat );
  if ( pushexception( status ) ) goto error3;

  return heap;

  error3:

  if ( heap->mode & IOShr ) {
    status = heap->proc->unlock( heap->data, 0, 1 );
    logexception( status );
  }

  if ( heap->dir != NULL ) free( heap->dir );

  error2:

  status = heap->proc->final( heap->data, E_HEAP_INIT );
  logexception( status );

  error1:

  free( heap );

  error0:

  if ( data != NULL ) free( data );

  return NULL;

}
