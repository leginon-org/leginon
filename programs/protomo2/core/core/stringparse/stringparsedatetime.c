/*----------------------------------------------------------------------------*
*
*  stringparsedatetime.c  -  core: character string operations
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

static Status StringGetDate
              (const char **str,
               uint32_t *date)

{
  const char *ptr = *str;
  uint32_t d = 0;
  Size i = 0;

  while ( i++ < 8 ) {
    if ( ( *ptr < '0' ) || ( *ptr > '9' ) ) {
      *str = ptr;
      return E_USER;
    }
    d <<= 4;
    d |= *ptr++ - '0';
  }
  *date = d;
  *str = ptr;
  return E_NONE;

}


static Status StringGetTime
              (const char **str,
               uint32_t *time)

{
  const char *ptr = *str;
  uint32_t h, m, s;
  Size i = 0;

  while ( i++ < 6 ) {
    if ( ( *ptr < '0' ) || ( *ptr > '9' ) ) {
      *str = ptr;
      return E_USER;
    }
    ptr++;
  }
  ptr = *str;
  h = *ptr++ - '0'; h *= 10; h += *ptr++ - '0';
  m = *ptr++ - '0'; m *= 10; m += *ptr++ - '0';
  s = *ptr++ - '0'; s *= 10; s += *ptr++ - '0';
  *str = ptr;
  if ( ( h >= 24 ) || ( m >=60 ) || ( s >= 60 ) ) {
    return E_USER;
  }
  *time = 1000 * ( s + 60 * ( m + 60 * h ) );
  return E_NONE;

}


static Status StringGetTimeFract
              (const char **str,
               uint32_t *time)

{
  const char *ptr = *str;
  uint32_t ms = 0;
  Size i = 0;

  while ( i++ < 3 ) {
    ms *= 10;
    if ( ( *ptr >= '0' ) && ( *ptr <= '9' ) ) {
      ms += *ptr++ - '0';
    }
  }
  *str = ptr;
  (*time) += ms;
  return E_NONE;

}


extern Status StringParseDateTime
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *ptr = str;
  Size dstsize = 0;
  Time val;
  Status status = E_STRINGPARSE_NOPARSE;

  if ( str == NULL ) {
    if ( param == NULL ) {
      status = exception( E_ARGVAL ); goto exit;
    } else {
      dstsize = sizeof( Time ); goto exit;
    }
  }

  if ( !StringGetDate( &ptr, &val.date )
    && !StringGetTime( &ptr, &val.time )
    && !StringGetTimeFract( &ptr, &val.time ) ) {

    Time *d = dst;
    if ( d != NULL ) {
      memcpy( d, &val, sizeof(Time) );
    }
    dstsize = sizeof( Time );
    str = ptr;
    status = E_NONE;

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
