/*----------------------------------------------------------------------------*
*
*  thread.h  -  core: posix threads
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef thread_h_
#define thread_h_

#include "defs.h"

#define ThreadName   "thread"
#define ThreadVers   COREVERS"."COREBUILD
#define ThreadCopy   CORECOPY


/* exception codes */

enum {
  E_THREAD = ThreadModuleCode,
  E_THREAD_INIT,
  E_THREAD_WAIT,
  E_THREAD_ERROR,
  E_THREAD_EOF,
  E_THREAD_MAXCODE
};


/* types */

typedef struct {
  Status status;
  Status (*function)(Size, const void *, void *);
  const void *inarg;
  void *outarg;
} Thread;


/* prototypes */

extern Size ThreadGetProcessors();

extern Size ThreadGetCount();

extern void ThreadSetCount
            (Size count);

extern Status ThreadExec
              (Size count,
               Thread *threads);

extern Status ThreadExecFn
              (Status (*function)(void *),
               Status (*getargs)(void *, void *),
               void *context,
               Size argsize);


#endif
