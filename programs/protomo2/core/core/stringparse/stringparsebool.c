/*----------------------------------------------------------------------------*
*
*  stringparsebool.c  -  core: character string operations
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


/* functions */

extern Status StringParseBool
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *StringFalse[] = { "0", "off", "false", "no", "n", NULL };
  const char *StringTrue[]  = { "1", "on",  "true",  "yes","y", NULL };
  StringParseParam par;
  Size dstsize = 0;
  Status status = E_NONE;

  if ( str == NULL ) {
    if ( param == NULL ) {
      status = exception( E_ARGVAL ); goto exit;
    } else {
      dstsize = sizeof( Bool ); goto exit;
    }
  }

  par.keyword.exact = True;
  par.keyword.extra = NULL;
  par.keyword.table = StringFalse;
  status = StringParseKeywordCase( str, end, NULL, &par );
  if ( status && ( status != E_STRINGPARSE_NOPARSE ) ) goto exit;

  if ( status == E_STRINGPARSE_NOPARSE ) {
    par.keyword.table = StringTrue;
    status = StringParseKeywordCase( str, end, NULL, &par );
    if ( status ) goto exit;
  }

  dstsize = sizeof( Bool );

  exit:

  if ( end != NULL ) {
    *end = str;
  }

  if ( param != NULL ) {
    param->dstsize = dstsize;
  }

  return status;

}
