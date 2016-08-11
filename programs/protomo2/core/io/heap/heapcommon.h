/*----------------------------------------------------------------------------*
*
*  heapcommon.h  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef heapcommon_h_
#define heapcommon_h_

#include "heap.h"


/* configuration */

#define HeapVersionMajor  ( '1' )
#define HeapVersionMinor  ( '1' )

#define HeapHdrSize  ( 16 )
#define HeapEntSize  ( 4 )
#define HeapTmpSize  ( 32 * 1024 )

#define HeapHdrInd   ( 0 * HeapEntSize )
#define HeapEndInd   ( 1 * HeapEntSize )
#define HeapDirInd   ( 2 * HeapEntSize )

#define HeapSegMin   ( 3 )
#define HeapSegInd   ( HeapSegMin * HeapEntSize )

#define HeapEntInc   ( 6 )
#define HeapEntMin   ( 8 )
#define HeapEntMax   ( UINT32_MAX / HeapEntSize )
#define HeapSegMax   ( INT64_MAX - sizeof(HeapAtom) )

#define HeapDirOffs  ( hdr[3] )
#define HeapDirSize  ( hdr[4] * HeapEntSize + 1 )
#define HeapDirCount ( hdr[4] )
#define HeapSegCount ( ( HeapDirCount < HeapSegMin ) ? 0 : HeapDirCount - HeapSegMin )

#define HeapTotSize  ( hdr[2] )
#define HeapHdrStat  ( hdr[5] )
#define HeapHdrCre   ( hdr[6] )
#define HeapHdrMod   ( hdr[7] )
#define HeapMetaMin  ( 8 )


/* macros */

#define HeapPrev( l )  ( (HeapIndex)((l)>>32) )
#define HeapNext( l )  ( (HeapIndex)(l) )

#define HeapLink( p, n )  ( (((HeapAtom)(p))<<32) | ((HeapIndex)(n)) )

#define DirLink( i )  ( dir[(i)+1] )
#define DirOffs( i )  ( dir[(i)+2] )
#define DirSize( i )  ( dir[(i)+3] )
#define DirMeta( i )  ( dir[(i)+4] )

#define DirPrev( i )  ( HeapPrev( DirLink( i ) ) )
#define DirNext( i )  ( HeapNext( DirLink( i ) ) )

#define SetPrev( i, p )     ( SetLink( i, p, DirNext( i ) ) )
#define SetNext( i, n )     ( SetLink( i, DirPrev( i ), n ) )
#define SetLink( i, p, n )  ( DirLink( i ) = HeapLink( p, n ) )

#define SetEnt( i, p, n, o, s, m )                    \
  {                                                   \
    HeapAtom *ptr = dir; ptr += ( i ) + 1;            \
    ptr[0] = HeapLink( p, n );                        \
    ptr[1] = ( o );                                   \
    ptr[2] = ( s );                                   \
    ptr[3] = ( m );                                   \
  }

#define ClrEnt( i )                                   \
  {                                                   \
    HeapAtom *ptr = dir; ptr += ( i ) + 1;            \
    ptr[0] = 0;                                       \
    ptr[1] = 0;                                       \
    ptr[2] = 0;                                       \
    ptr[3] = 0;                                       \
  }

#define IOModeErr 0x1000


/* types */

typedef uint64_t HeapAtom;
typedef uint32_t HeapIndex;
#define HeapAtomU  PRIu64
#define HeapAtomX  PRIx64
#define HeapIndexU PRIu32
#define HeapIndexX PRIx32

typedef enum {
  HeapStatOpen = 0x01,
  HeapStatSync = 0x02,
  HeapStatSerr = 0x04,
  HeapStatBigE = 0x10,
  HeapStatMask = 0xff,
  HeapStatPack = 0x0100,
  HeapStatDbuf = 0x0200,
  HeapStatNest = 0x1000,
} HeapStat;

struct _Heap {
  void *data;
  const HeapProc *proc;
  IOMode mode;
  HeapStat stat;
  HeapAtom hdr[HeapHdrSize];
  HeapAtom *dir;
  Offset size;
  Size nestcount;
  Size objcount;
  HeapAtom tmp[HeapTmpSize];
};


/* prototypes */

extern void HeapPack
            (Size count,
             const HeapAtom *src,
             void *dst);

extern void HeapUnpack
            (Size count,
             const void *src,
             HeapAtom *dst);

extern Status HeapRead
              (Heap *heap,
               HeapAtom offs,
               HeapAtom *dst,
               Size count);

extern Status HeapWrite
              (Heap *heap,
               HeapAtom offs,
               const HeapAtom *src,
               Size count);

extern Status HeapClear
              (Heap *heap,
               HeapAtom offs,
               HeapAtom size);

extern Status HeapExtend
              (Heap *heap,
               HeapAtom *hdr,
               HeapAtom *dir,
               HeapAtom size,
               HeapIndex *seg,
               HeapAtom *offs,
               HeapAtom *allo);

extern Status HeapSync
              (Heap *heap,
               HeapAtom *hdr,
               HeapAtom *dir);

extern Status HeapHdrSync
              (Heap *heap,
               HeapAtom *hdr,
               HeapAtom stat);

extern void HeapMod
            (Heap *heap,
             HeapAtom *hdr);

extern void HeapErr
            (Heap *heap,
             HeapAtom *hdr,
             HeapAtom *dir);

extern Status HeapDirRead
              (Heap *heap);

extern Status HeapDirWrite
              (Heap *heap,
               const HeapAtom *hdr,
               const HeapAtom *dir);

extern Status HeapDirCheck
              (const HeapAtom *hdr,
               const HeapAtom *dir,
               HeapAtom *tmp);

extern Status HeapDirCheckEnt
              (const HeapAtom *hdr,
               const HeapAtom *dir);

extern Status HeapDirCheckLinks
              (const HeapAtom *hdr,
               const HeapAtom *dir,
               HeapAtom *tmp);

extern Status HeapDirAlloc
              (Heap *heap,
               HeapAtom *hdr,
               HeapAtom **ptr,
               HeapIndex *seg,
               HeapIndex ind);

extern Status HeapSegSearch
              (const HeapAtom *dir,
               HeapAtom dircount,
               HeapAtom size,
               HeapIndex *entr,
               HeapIndex *free,
               HeapAtom *offs,
               HeapAtom *allo);

extern void HeapSegMerge
            (HeapAtom *dir);

extern void HeapSegSplit
            (HeapAtom *dir,
             HeapIndex ent,
             HeapIndex seg,
             HeapAtom size,
             HeapAtom allo);

extern void HeapSegSwap
            (HeapAtom *dir,
             HeapIndex ind1,
             HeapIndex ind2,
             HeapAtom size2,
             HeapAtom meta2);


#endif
