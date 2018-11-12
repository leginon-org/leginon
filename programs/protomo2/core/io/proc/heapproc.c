/*----------------------------------------------------------------------------*
*
*  heapproc.c  -  io: heap procedures
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "heapproccommon.h"
#include "heapcommon.h"
#include "exception.h"


/* functions */

static Status HeapNullAddr
              (void *heapdata,
               Offset offset,
               Size size,
               void **buf)

{

  return exception( E_HEAPPROC_NUL );

}


static Status HeapNullRead
              (void *heapdata,
               Offset offset,
               Size size,
               void *buf)

{

  return exception( E_HEAPPROC_NUL );

}


static Status HeapNullWrite
              (void *heapdata,
               Offset offset,
               Size size,
               const void *buf)

{

  return exception( E_HEAPPROC_NUL );

}


extern Status HeapNullResize
              (void *heapdata,
               Offset *oldsize,
               Offset newsize)

{

  return exception( E_HEAPPROC_NUL );

}


extern Status HeapNullSync
              (void *heapdata)

{

  return exception( E_HEAPPROC_NUL );

}


extern Status HeapNullFinal
              (void *heapdata,
               Status fail)

{

  return exception( E_HEAPPROC_NUL );

}


/* variables */

static const HeapProc HeapProcNullStruct = {
  NULL,
  HeapNullAddr,
  HeapNullRead,
  HeapNullWrite,
  HeapNullResize,
  NULL,
  NULL,
  HeapNullSync,
  HeapNullFinal,
};

const HeapProc *HeapProcNull = &HeapProcNullStruct;
