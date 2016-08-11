/*----------------------------------------------------------------------------*
*
*  heapprocmodule.c  -  io: heap procedures
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
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage HeapProcExceptions[ E_HEAPPROC_MAXCODE - E_HEAPPROC ] = {
  { "E_HEAPPROC",     "internal error ("HeapProcName")" },
  { "E_HEAPPROC_NUL", "unimplemented operation" },
  { "E_HEAPPROC_OFF", "invalid i/o operation (offset/size)" },
  { "E_HEAPPROC_MMP", "memory mapping error" },
  { "E_HEAPPROC_DEL", "delete on close" },
};


/* variables */

const HeapFileProc *HeapFileProcDefault;


/* module initialization/finalization */

static Status HeapProcModuleInit
              (void **data)

{
  static HeapFileProc proc;
  Status status;

  status = ExceptionRegister( HeapProcExceptions, E_HEAPPROC, E_HEAPPROC_MAXCODE );
  if ( exception( status ) ) return status;

  proc.sys = HeapProcGetSys( NULL );
  proc.std = HeapProcGetStd( NULL );
  proc.mmap = HeapProcGetMmap( NULL );

  HeapFileProcDefault = &proc;

  return status;

}


/* module descriptor */

const Module HeapProcModule = {
  HeapProcName,
  HeapProcVers,
  HeapProcCopy,
  COMPILE_DATE,
  HeapProcModuleInit,
  NULL,
  NULL,
};
