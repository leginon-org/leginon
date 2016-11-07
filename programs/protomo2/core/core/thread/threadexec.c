/*----------------------------------------------------------------------------*
*
*  threadexec.c  -  core: posix threads
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



extern Status ThreadExec
              (Size count,
               Thread *threads)

{
  Status status = E_NONE;

  if ( argcheck( threads == NULL ) ) return exception( E_ARGVAL );

  for ( Size t = 0; t < count; t++ ) {
    threads[t].status = E_THREAD_WAIT;
  }

  Size max = 1;

  if ( ( max <= 1 ) || ( count <= 1 ) ) {

    for ( Size t = 0; t < count; t++ ) {

      if ( SignalInterrupt ) return exception( E_SIGNAL );

      threads[t].status = threads[t].function( t, threads[t].inarg, threads[t].outarg );
      if ( threads[t].status ) return exception( E_THREAD_ERROR );

    }

  } else {

  }

  return status;

}
