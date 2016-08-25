/*----------------------------------------------------------------------------*
*
*  stringparseuint32.c  -  core: character string operations
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

static uint32_t StringParseGetVal
                (char c,
                 uint32_t base)

{

  if ( c >= '0' ) {
    if ( c <= '9' ) return c - '0';
    if ( c >= 'A' ) {
      if ( c <= 'Z' ) return c - 'A' + 10;
      if ( c >= 'a' ) {
        if ( c <= 'Z' ) return c - 'a' + 36;
      }
    }
  }

  return UINT32_MAX;

}


extern Status StringParseUint32
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *num, *ptr = str;
  Size dstsize = 0;
  uint32_t base = 10;
  uint32_t dig, new, val = 0;
  Status status = E_NONE;

  if ( str == NULL ) {
    if ( param == NULL ) {
      status = exception( E_ARGVAL ); goto exit;
    } else {
      dstsize = sizeof( uint32_t ); goto exit;
    }
  }

  if ( param != NULL ) {
    if ( ( param->number.base == 1 ) || ( param->number.base > 62 ) ) {
      status = exception( E_ARGVAL ); goto exit;
    }
    if ( param->number.base ) base = param->number.base;
  }

  if ( *ptr == '+' ) ptr++;
  num = ptr;

  while ( ( dig = StringParseGetVal( *ptr, base ) ) < base ) {
    new = val * base;
    if ( new / base != val ) {
      status = E_INTOVFL; break;
    }
    val = new + dig;
    if ( val < new ) {
      status = E_INTOVFL; break;
    }
    ptr++;
  }

  if ( status ) {
    while ( StringParseGetVal( *ptr, base ) >= base ) ptr++;
    val = UINT32_MAX;
  }

  if ( ptr == num ) {

    status = E_STRINGPARSE_NOPARSE;

  } else {

    uint32_t *d = dst;
    if ( d != NULL ) {
      *d = val;
    }
    dstsize = sizeof( uint32_t );
    str = ptr;

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
