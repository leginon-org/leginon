/*----------------------------------------------------------------------------*
*
*  threadexecfn.c  -  core: posix threads
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


/* types */

typedef struct {
  pthread_mutex_t mutex;
  pthread_attr_t attr;
  Status *status;
  Size maxproc;
  Status (*function)(void *);
  Status (*getargs)(void *, void *);
  void *context;
  Size argsize;
  char *argbuf;
} ThreadGroup;


/* functions */


extern Status ThreadExecFn
              (Status (*function)(void *),
               Status (*getargs)(void *, void *),
               void *context,
               Size argsize)

{
  Status status = E_NONE;

  if ( argcheck( function == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( getargs  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( argsize == 0 ) ) return exception( E_ARGVAL );

  Size max = 1;

  argsize = ( argsize + 7 ) / 8;
  char *args = malloc( max * argsize );
  if ( args == NULL ) return exception( E_MALLOC );

  if ( max <= 1 ) {

    while ( True ) {

      if ( SignalInterrupt ) { status = exception( E_SIGNAL ); break; }

      status = getargs( context, args );
      if ( status == E_THREAD_EOF ) { status = E_NONE; break; }
      if ( exception( status ) ) break;

      status = function( args );
      if ( status ) { status = exception( E_THREAD_ERROR ); break; }

    }

  } else {

  }

  free( args );

  return status;

}
