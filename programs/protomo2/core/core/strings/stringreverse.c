/*----------------------------------------------------------------------------*
*
*  stringreverse.c  -  core: character string operations
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
#include <string.h>


/* functions */

extern void StringReverse
            (char *str)

{

  if ( ( str == NULL ) || !*str ) return;

  char *end = str + strlen( str ) - 1;

  while ( str < end ) {
    char c = *str;
    *str++ = *end;
    *end-- = c;
  }

}
