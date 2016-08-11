/*----------------------------------------------------------------------------*
*
*  stringparsekeywordcase.c  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "stringparse.h"
#include "exception.h"
#include <ctype.h>
#include <string.h>


/* functions */

extern Status StringParseKeywordCase
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char **table;
  Size i = 0;
  Size dstsize = 0;
  Status status = E_STRINGPARSE_NOPARSE;

  if ( ( str == NULL ) || ( param == NULL ) ) {
    status = exception( E_ARGVAL ); goto exit;
  }
  table = param->keyword.table;
  if ( table == NULL ) {
    status = exception( E_ARGVAL ); goto exit;
  }

  while ( table[i] != NULL ) {

    const char *tab = table[i++];
    const char *ptr = str;

    while ( *tab && ( tolower(*tab) == tolower(*ptr) ) ) {
      tab++; ptr++;
    }

    if ( *tab ) continue;
    if ( isalpha( *ptr ) ) continue;
    if ( *ptr ) {
      if ( param->keyword.exact ) continue;
      if ( ( param->keyword.extra != NULL) && ( strchr( param->keyword.extra, *ptr ) != NULL ) ) continue;
    }

    if ( ptr != str ) {
      Size *d = dst;
      if ( d != NULL ) {
        *d = i - 1;
      }
      dstsize = sizeof(Size);
      str = ptr;
      status = E_NONE;
      break;
    }

  }

  exit:

  if ( end != NULL ) {
    *end = str;
  }

  if ( param != NULL ) {
    param->dstsize = dstsize;
  }

  return status;

}
