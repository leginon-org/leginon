/*----------------------------------------------------------------------------*
*
*  stringparsereal64.c  -  core: character string operations
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
#include <stdlib.h>


/* functions */

extern Status StringParseReal64
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *ptr = str;
  Size dstsize = 0;
  Real64 val;
  Status status = E_NONE;

  if ( str == NULL ) {
    if ( param == NULL ) {
      status = exception( E_ARGVAL ); goto exit;
    } else {
      dstsize = sizeof( Real64 ); goto exit;
    }
  }

  errno = 0;
  val = strtod( str, (char **)&ptr );

  if ( ptr == str ) {

    status = E_STRINGPARSE_NOPARSE;

  } else {

    Real64 *d = dst;
    if ( d != NULL ) {
      *d = val;
    }
    dstsize = sizeof( Real64 );
    str = ptr;

    if ( errno ) {
      if ( val == 0 ) {
        status = E_FLTUNFL;
      } else {
        status = E_FLTOVFL;
      }
    } else {
      status = E_NONE;
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
