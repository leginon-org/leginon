/*----------------------------------------------------------------------------*
*
*  stringparseimag32.c  -  core: character string operations
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

extern Status StringParseImag32
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *ptr = str;
  Size dstsize = 0;
  double val;
  Status status = E_NONE;

  if ( str == NULL ) {
    if ( param == NULL ) {
      status = exception( E_ARGVAL ); goto exit;
    } else {
      dstsize = sizeof( Real32 ); goto exit;
    }
  }

  errno = 0;
  val = strtod( str, (char **)&ptr );

  if ( ( ptr == str ) || ( *ptr != 'i' ) ) {

    status = E_STRINGPARSE_NOPARSE;

  } else {

    Real32 fval, *d = dst;

    if ( errno ) {

      if ( val == 0 ) {
        fval = 0;
        status = E_FLTUNFL;
      } else {
        if ( val < 0 ) {
          fval = -Real32Max;
        } else {
          fval = Real32Max;
        }
        status = E_FLTOVFL;
      }

    } else {

      if ( val < -Real32Max ) {
        fval = -Real32Max;
        status = E_FLTOVFL;
      } else if ( val > Real32Max ) {
        fval = Real32Max;
        status = E_FLTOVFL;
      } else {
        fval = val;
        if ( ( fval == 0 ) && ( val != 0 ) ) {
          status = E_FLTUNFL;
        }
      }

    }

    if ( d != NULL ) {
      *d = fval;
    }
    dstsize = sizeof( Real32 );
    str = ++ptr;

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
