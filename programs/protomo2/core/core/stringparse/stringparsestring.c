/*----------------------------------------------------------------------------*
*
*  stringparsestring.c  -  core: character string operations
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
#include <string.h>


/* functions */

extern Status StringParseString
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *ptr = str;
  Size dstsize = 0;
  Status status = E_STRINGPARSE_NOPARSE;

  if ( str == NULL ) {
    status = exception(E_ARGVAL); goto exit;
  }

  if ( ( param != NULL ) && ( param->string.ptr != NULL ) ) {

    const char *string = param->string.ptr;

    while ( *string && ( *string == *ptr ) ) {
      string++; ptr++;
    }

    if ( !*string ) {

      dstsize = ptr - str;
      if ( dstsize ) {
        if ( dst != NULL ) {
          memcpy( dst, str, dstsize );
        }
        str = ptr;
        status = E_NONE;
      }

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
