/*----------------------------------------------------------------------------*
*
*  heapproc.h  -  io: heap procedures
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef heapproc_h_
#define heapproc_h_

#include "heap.h"
#include "fileio.h"

#define HeapProcName   "heapproc"
#define HeapProcVers   IOVERS"."IOBUILD
#define HeapProcCopy   IOCOPY


/* exception codes */

enum {
  E_HEAPPROC = HeapProcModuleCode,
  E_HEAPPROC_NUL,
  E_HEAPPROC_OFF,
  E_HEAPPROC_MMP,
  E_HEAPPROC_DEL,
  E_HEAPPROC_MAXCODE
};


/* types */

typedef struct {
  const HeapProc *sys;
  const HeapProc *std;
  const HeapProc *mmap;
} HeapFileProc;

typedef struct {
  const HeapFileProc *defaultproc;
  const HeapFileProc *proc;
  HeapParam *param;
  Offset offs;
  Offset size;
} HeapFileParam;


/* constants */

#define HeapFileProcInitializer   (HeapFileProc){ NULL, NULL, NULL }

#define HeapFileParamInitializer  (HeapFileParam){ NULL, NULL, NULL, -1, -1 }


/* variables */

extern const HeapFileProc *HeapFileProcDefault;


/* prototypes */

extern Heap *HeapMemCreate
             (const HeapParam *param);

extern Status HeapMemDestroy
              (Heap *heap);

extern Heap *HeapFileInit
             (Fileio *fileio,
              const HeapFileParam *param);

extern Heap *HeapNestInit
             (Heap *heap,
              int segm,
              HeapMeta meta,
              const HeapParam *param);


#endif
