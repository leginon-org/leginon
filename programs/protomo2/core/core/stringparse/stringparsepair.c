/*----------------------------------------------------------------------------*
*
*  stringparsepair.c  -  core: character string operations
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

#define PLEN 32


/* functions */

extern Status StringParsePair
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *ptr = str;
  const char *cur;
  char pair[2*PLEN];
  Size dstsize = 0;
  Status status;

  if ( ( str == NULL ) || ( param == NULL ) || ( param->pair.parse == NULL ) ) {
    status = exception( E_ARGVAL ); goto exit;
  }

  status = param->pair.parse( NULL, NULL, NULL, param );
  if ( exception( status ) ) goto exit;
  Size size = param->dstsize;
  if ( size > PLEN ) {
    status = exception( E_STRINGPARSE_ERROR ); goto exit;
  }

  if ( str == NULL ) {
    dstsize = 2 * size; goto exit;
  }

  Bool space = param->pair.space;
  char sep = param->pair.sep;
  if ( !sep && !ispunct( sep ) ) {
    status = exception( E_STRINGPARSE_SEPAR ); goto exit;
  } else if ( isspace( sep ) ) {
    space = True; sep = 0;
  }

  if ( space ) {
    while ( isspace( *ptr ) ) ptr++;
  }

  status = param->pair.parse( ptr, &ptr, pair, NULL );
  if ( status ) goto exit;

  cur = ptr;
  if ( space ) {
    while ( isspace( *ptr ) ) ptr++;
  }
  if ( sep ) {
    cur = ptr;
    if ( *ptr == sep ) {
      ptr++;
      if ( space ) {
        while ( isspace( *ptr ) ) ptr++;
      }
    }
  }

  if ( cur == ptr ) {
    if ( param->pair.single ) {
      memcpy( pair + size, pair, size ); goto exit2;
    }
    status = E_STRINGPARSE_NOPARSE; goto exit;
  }

  status = param->pair.parse( ptr, &ptr, pair + size, NULL );
  if ( status ) goto exit;

  if ( space ) {
    while ( isspace( *ptr ) ) ptr++;
  }

  exit2:

  dstsize = 2 * size;
  if ( dst != NULL ) {
    memcpy( dst, pair, dstsize );
  }
  str = ptr;

  exit:

  if ( end != NULL ) {
    *end = str;
  }

  if ( param != NULL ) {
    param->dstsize = dstsize;
  }

  return status;

}

