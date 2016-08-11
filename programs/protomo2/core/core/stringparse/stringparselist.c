/*----------------------------------------------------------------------------*
*
*  stringparselist.c  -  core: character string operations
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

extern Status StringParseList
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *cur, *ptr = str;
  Size count = 0, size = 0, dstsize = 0;
  char *dstptr = dst;
  Status status = E_STRINGPARSE_NOPARSE;

  if ( ( str == NULL ) || ( param == NULL ) || ( param->list.parse == NULL ) ) {
    status = exception( E_ARGVAL ); goto exit;
  }

  if ( param->list.param == NULL ) {
    StringParseParam paramlist;
    status = param->list.parse( NULL, NULL, NULL, &paramlist );
    if ( status ) goto exit;
    size = paramlist.dstsize;
  }

  Bool space = param->list.space;
  char sep = param->list.sep;
  if ( isspace( sep ) ) {
    space = True; sep = 0;
  } else if ( sep && !ispunct( sep ) ) {
    status = exception( E_STRINGPARSE_SEPAR ); goto exit;
  }

  cur = ptr;
  if ( space ) {
    while ( isspace( *ptr ) ) ptr++;
  }

  for ( count = 0; count < param->list.count; count++ ) {

    if ( count ) {
      cur = ptr;
      if ( space ) {
        while ( isspace( *ptr ) ) ptr++;
      }
      if ( !*ptr ) break;
      if ( sep ) {
        cur = ptr;
        if ( *ptr == sep ) {
          ptr++;
          if ( space ) {
            while ( isspace( *ptr ) ) ptr++;
          }
          if ( !*ptr ) {
            str = cur; goto exit2;
          }
        }
      }
      if ( cur == ptr ) {
        status = E_STRINGPARSE_ERROR; goto exit;
      }
    }

    status = param->list.parse( ptr, &ptr, dstptr, param->list.param );
    if ( status ) {
      if ( status == E_STRINGPARSE_NOPARSE ) {
        if ( dstsize ) status = E_NONE;
      }
      str = cur; goto exit2;
    }

    if ( param->list.param != NULL ) {
      if ( size ) {
        if ( size != param->list.param->dstsize ) {
          status = E_STRINGPARSE; goto exit;
        }
      } else {
        size = param->list.param->dstsize;
      }
    }

    if ( dstptr != NULL ) {
      dstptr += size;
    }

  }

  str = ptr;

  exit2: dstsize = count * size;

  exit:

  if ( end != NULL ) {
    *end = str;
  }

  if ( param != NULL ) {
    param->dstsize = dstsize;
    param->list.count = count;
  }

  return status;

}
