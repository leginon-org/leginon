/*----------------------------------------------------------------------------*
*
*  stringconcat.c  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "strings.h"
#include "exception.h"
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>


/* functions */

extern char *StringConcat
             (const char *str, ...)

{
  Size len = 1;

  if ( str != NULL ) {
    va_list ap;
    va_start( ap, str );
    const char *s = str;
    do {
      len += strlen( s );
      s = va_arg( ap, const char * );
    } while ( s != NULL );
    va_end( ap );
  }

  char *new = malloc( len );
  if ( new == NULL ) {
    logexception( E_MALLOC );
  } else {
    va_list ap;
    va_start( ap, str );
    const char *s = str;
    char *n = new;
    while ( s != NULL ) {
      while ( *s ) {
        *n++ = *s++;
      }
      s = va_arg( ap, const char * );
    }
    *n = 0;
    va_end( ap );
  }

  return new;

}
