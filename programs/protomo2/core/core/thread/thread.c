/*----------------------------------------------------------------------------*
*
*  thread.c  -  core: posix threads
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
#include "macros.h"
#include "signals.h"
#include <stdlib.h>
#include <unistd.h>


/* variables */

static Size ThreadMax = 1;


/* functions */


extern Size ThreadGetProcessors()

{
  long int proc = 1;

#ifdef _SC_NPROCESSORS_CONF
  proc = sysconf( _SC_NPROCESSORS_CONF );
#elif _SC_NPROC_CONF
  proc = sysconf( _SC_NPROC_CONF );
#endif

  return proc;

}


extern Size ThreadGetCount()

{
  Size count;


  count = ThreadMax;

  return count;

}


extern void ThreadSetCount
            (Size count)

{

  ThreadMax = count ? count : ThreadGetProcessors();

}
