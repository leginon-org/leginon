/*----------------------------------------------------------------------------*
*
*  strings.c  -  core: character string operations
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
#include <ctype.h>
#include <stdlib.h>


/* functions */

extern char **StringSeparate
              (const char *str,
               char sep)

{
  const char *ptr, *end;
  char *new;

  if ( isspace( sep ) ) {
    sep = 0;
  } else if ( sep && !ispunct( sep ) ) {
    return NULL;
  }

  char **list = malloc( sizeof(char *));
  if ( list == NULL ) return NULL;
  list[0] = NULL;

  if ( str == NULL ) return list;

  if ( sep ) {

    for ( Size i = 0; *str; i++ ) {

      if ( i ) str++;

      while ( isspace( *str ) ) str++;
      if ( !i && !*str ) break;

      if ( *str == sep ) {
        ptr = str + 1;
        end = str;
      } else {
        ptr = str;
        while ( *str && ( *str != sep ) ) str++;
        end = str;
        while ( ( end > ptr ) && isspace( *--end ) );
      }

      char **lst = realloc( list, ( i + 2 ) * sizeof(char *) );
      if ( lst == NULL ) goto error;
      list = lst;

      Size len = end + 1 - ptr;
      new = malloc( len + 1 );
      if ( new == NULL ) goto error;

      list[i] = new;
      list[i+1] = NULL;

      while ( ptr <= end ) *new++ = *ptr++;
      *new = 0;

    }

  } else {

    for ( Size i = 0; *str; i++ ) {

      while ( isspace( *str ) ) str++;
      if ( !*str ) break;

      ptr = str;
      while ( *str && !isspace( *str ) ) str++;

      char **lst = realloc( list, ( i + 2 ) * sizeof(char *) );
      if ( lst == NULL ) goto error;
      list = lst;

      Size len = str - ptr;
      new = malloc( len + 1 );
      if ( new == NULL ) goto error;

      list[i] = new;
      list[i+1] = NULL;

      while ( ptr < str ) *new++ = *ptr++;
      *new = 0;

    }

  }

  return list;

  error: StringListFree( list );

  return NULL;

}
