/*----------------------------------------------------------------------------*
*
*  stringparseident.c  -  core: character string operations
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

extern Status StringParseIdent
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *ptr = str;
  Size dstsize = 0;
  Status status;

  if ( str == NULL ) {
    status = exception(E_ARGVAL); goto exit;
  }

  if ( ( param == NULL ) || ( param->ident.extra == NULL ) ) {

    if ( isalpha( *ptr ) ) {
      do ptr++; while ( isalpha( *ptr ) );
    }

  } else {

    if ( isalpha( *ptr ) ) {
      do ptr++; while ( isalpha( *ptr ) || ( strchr( param->ident.extra, *ptr ) != NULL ) );
    }

  }

  dstsize = ptr - str;
  if ( dstsize ) {
    if ( dst != NULL ) {
      memcpy( dst, str, dstsize );
    }
    status = E_NONE;
  } else {
    status = E_STRINGPARSE_NOPARSE;
  }

  exit:

  if ( end != NULL ) {
    *end = ptr;
  }

  if ( param != NULL ) {
    param->dstsize = dstsize;
  }

  return status;

}
