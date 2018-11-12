/*----------------------------------------------------------------------------*
*
*  heapproccommon.h  -  io: heap procedures
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef heapproccommon_h_
#define heapproccommon_h_

#include "heapproc.h"


/* types */

typedef struct {
  void *handle;
  int segm;
  Offset offs;
  Offset size;
  IOMode mode;
} HeapData;


/* constants */

#define HeapDataInitializer  (HeapData){ NULL, -1, -1, -1, 0 }


/* variables */

extern const HeapProc *HeapProcNull;

extern const HeapProc *HeapProcMem;

extern const HeapProc *HeapProcNest;


/* prototypes */

extern const HeapProc *HeapProcGetSys
                       (const HeapFileProc *proc);

extern const HeapProc *HeapProcGetStd
                       (const HeapFileProc *proc);

extern const HeapProc *HeapProcGetMmap
                       (const HeapFileProc *proc);

extern Status HeapFileResizeSub
              (HeapData *data,
               Offset *oldsize,
               Offset newsize);

extern Status HeapFileResize
              (void *heapdata,
               Offset *oldsize,
               Offset newsize);

extern Status HeapFileSync
              (void *heapdata);

extern Status HeapFileFinal
              (void *heapdata,
               Status fail);


#endif
