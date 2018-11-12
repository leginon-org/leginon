/*----------------------------------------------------------------------------*
*
*  threadmodule.c  -  core: posix threads
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "threadcommon.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ThreadExceptions[ E_THREAD_MAXCODE - E_THREAD ] = {
  { "E_THREAD",       "internal error ("ThreadName")" },
  { "E_THREAD_INIT",  "thread initialization error" },
  { "E_THREAD_WAIT",  "thread not started"     },
  { "E_THREAD_ERROR", "thread error condition" },
  { "E_THREAD_EOF",   "thread end of file" },
};


/* module initialization/finalization */

static Status ThreadModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ThreadExceptions, E_THREAD, E_THREAD_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module ThreadModule = {
  ThreadName,
  ThreadVers,
  ThreadCopy,
  COMPILE_DATE,
  ThreadModuleInit,
  NULL,
  NULL,
};
