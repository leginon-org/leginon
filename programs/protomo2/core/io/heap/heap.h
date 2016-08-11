/*----------------------------------------------------------------------------*
*
*  heap.h  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef heap_h_
#define heap_h_

#include "iodefs.h"

#define HeapName   "heap"
#define HeapVers   IOVERS"."IOBUILD
#define HeapCopy   IOCOPY


/* exception codes */

enum {
  E_HEAP = HeapModuleCode,
  E_HEAP_INIT,
  E_HEAP_FIN,
  E_HEAP_USE,
  E_HEAP_META,
  E_HEAP_FMT,
  E_HEAP_SYN,
  E_HEAP_ERR,
  E_HEAP_MOD,
  E_HEAP_WR,
  E_HEAP_DIR,
  E_HEAP_SIZE,
  E_HEAP_SEGM,
  E_HEAP_EXIST,
  E_HEAP_MAXCODE
};


/* types */

struct _Heap;

typedef struct _Heap Heap;

typedef struct {
  Status (*init)( void * );
  Status (*addr)( void *, Offset, Size, void ** );
  Status (*read)( void *, Offset, Size, void * );
  Status (*write)( void *, Offset, Size, const void * );
  Status (*resize)( void *, Offset *, Offset );
  Status (*lock)( void *, Offset, Size );
  Status (*unlock)( void *, Offset, Size );
  Status (*sync)( void * );
  Status (*final)( void *, Status );
} HeapProc;

typedef struct {
  Size initsegm;
  Offset initsize;
  IOMode mode;
} HeapParam;

typedef uint64_t HeapMeta;


/* constants */

#define HeapProcInitializer   (HeapProc){ NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL }

#define HeapParamInitializer  (HeapParam){ 0, 0, IORd }


/* prototypes */

extern HeapMeta *HeapFormat
                 (void *buf,
                  Size len);

extern Heap *HeapInit
             (const HeapProc *proc,
              void *data,
              const HeapParam *param);

extern Status HeapFinal
              (Heap *heap,
               Status fail);

extern Status HeapFlush
              (Heap *heap);

extern Status HeapNew
              (Heap *heap,
               Offset size,
               HeapMeta meta,
               int *segm,
               Offset *offs);

extern Status HeapAlloc
              (Heap *heap,
               int segm,
               Offset size,
               HeapMeta meta,
               Offset *offs);

extern Status HeapDealloc
              (Heap *heap,
               int segm);

extern Status HeapResize
              (Heap *heap,
               int segm,
               Offset size,
               Offset *offs);

extern Status HeapAccess
              (Heap *heap,
               int segm,
               Offset *offs,
               Offset *size,
               HeapMeta *meta);

extern Status HeapMetaSet
              (Heap *heap,
               int index,
               HeapMeta meta);

extern Status HeapMetaGet
              (Heap *heap,
               int index,
               HeapMeta *meta);

extern Bool HeapGetSwap
            (Heap *heap);

extern IOMode HeapGetMode
              (Heap *heap);

extern Status HeapGetTime
              (Heap *heap,
               Time *cre,
               Time *mod);

extern Offset HeapGetSize
              (Heap *heap);

extern Status HeapStatSegm
              (Heap *heap,
               Offset *num,
               Offset *min,
               Offset *max,
               Offset *tot);

extern Status HeapStatAlloc
              (Heap *heap,
               Offset *num,
               Offset *min,
               Offset *max,
               Offset *tot);

extern Status HeapStatFree
              (Heap *heap,
               Offset *num,
               Offset *min,
               Offset *max,
               Offset *tot);


#endif
