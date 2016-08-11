/*----------------------------------------------------------------------------*
*
*  message.c  -  core: print diagnostic/error messages
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "message.h"
#include "baselib.h"
#include <stdarg.h>
#include <stdio.h>


/* functions */

extern void MessageStringLock()

{

}


extern void MessageStringUnlock()

{

}


extern void MessageString
            (const char *msg, ...)

{

  fflush( stderr );

  fputs( Main, stderr );
  fputs( ": ", stderr );

  if ( msg != NULL ) {

    va_list ap;
    va_start( ap, msg );

    while ( msg != NULL ) {

      fputs( msg, stderr );

      msg = va_arg( ap, const char * );

    }

    va_end( ap );

  }

  fflush( stderr );

}


extern void MessageStringBegin
            (const char *msg, ...)

{

  fflush( stderr );

  fputs( Main, stderr );
  fputs( ": ", stderr );

  if ( msg != NULL ) {

    va_list ap;
    va_start( ap, msg );

    while ( msg != NULL ) {

      fputs( msg, stderr );

      msg = va_arg( ap, const char * );

    }

    va_end( ap );

  }

}


extern void MessageStringHeadr
            (const char *msg, ...)

{

  fputs( Main, stderr );
  fputs( ": ", stderr );

  if ( msg != NULL ) {

    va_list ap;
    va_start( ap, msg );

    while ( msg != NULL ) {

      fputs( msg, stderr );

      msg = va_arg( ap, const char * );

    }

    va_end( ap );

  }

}


extern void MessageStringPrint
            (const char *msg, ...)

{

  if ( msg != NULL ) {

    va_list ap;
    va_start( ap, msg );

    while ( msg != NULL ) {

      fputs( msg, stderr );

      msg = va_arg( ap, const char * );

    }

    va_end( ap );

  }

}


extern void MessageStringEnd
            (const char *msg, ...)

{

  if ( msg != NULL ) {

    va_list ap;
    va_start( ap, msg );

    while ( msg != NULL ) {

      fputs( msg, stderr );

      msg = va_arg( ap, const char * );

    }

    va_end( ap );

  }

  fflush( stderr );

}


extern void MessageFormat
            (const char *fmt, ...)

{

  fflush( stderr );

  fputs( Main, stderr );
  fputs( ": ", stderr );

  if ( fmt != NULL ) {

    va_list ap;
    va_start( ap, fmt );

    vfprintf( stderr, fmt, ap );

  }

  fflush( stderr );

}


extern void MessageFormatBegin
            (const char *fmt, ...)

{

  fflush( stderr );

  fputs( Main, stderr );
  fputs( ": ", stderr );

  if ( fmt != NULL ) {

    va_list ap;
    va_start( ap, fmt );

    vfprintf( stderr, fmt, ap );

  }

}


extern void MessageFormatHeadr
            (const char *fmt, ...)

{

  fputs( Main, stderr );
  fputs( ": ", stderr );

  if ( fmt != NULL ) {

    va_list ap;
    va_start( ap, fmt );

    vfprintf( stderr, fmt, ap );

  }

}


extern void MessageFormatPrint
            (const char *fmt, ...)

{

  if ( fmt != NULL ) {

    va_list ap;
    va_start( ap, fmt );

    vfprintf( stderr, fmt, ap );

  }

}


extern void MessageFormatEnd
            (const char *fmt, ...)

{

  if ( fmt != NULL ) {

    va_list ap;
    va_start( ap, fmt );

    vfprintf( stderr, fmt, ap );

  }

  fflush( stderr );

}
