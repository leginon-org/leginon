/*----------------------------------------------------------------------------*
*
*  stringparserange.c  -  core: character string operations
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

#define RNGLEN 32


/* functions */

extern Status StringParseRange
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *ptr = str;
  char rng1[RNGLEN], rng2[RNGLEN];
  Size dstsize = 0;
  Bool dotdot = False;
  Size size, size1 = 0, size2 = 0;
  Status stat1 = E_STRINGPARSE_NOPARSE;
  Status stat2 = E_STRINGPARSE_NOPARSE;
  Status status;

  if ( ( str == NULL ) || ( param == NULL ) || ( param->range.parse == NULL ) ) {
    status = exception( E_ARGVAL ); goto exit;
  }

  status = param->range.parse( NULL, NULL, NULL, param );
  if ( exception( status ) ) goto exit;
  size = param->dstsize;
  if ( size > RNGLEN ) {
    status = exception( E_STRINGPARSE_ERROR ); goto exit;
  }

  status = E_STRINGPARSE_NOPARSE;

  if ( *ptr == '[' ) {

    /* parse lower limit */
    do ptr++; while ( isspace( *ptr ) );
    stat1 = param->range.parse( ptr, &ptr, rng1, NULL );
    if ( stat1 != E_STRINGPARSE_NOPARSE ) {
      if ( stat1 ) status = stat1;
      size1 = size;
      while ( isspace( *ptr ) ) ptr++;
    }

    if ( *ptr == '.' ) {

      if ( *++ptr == '.' ) {

        /* dot dot specified, parse upper limit */
        do ptr++; while ( isspace( *ptr ) );
        stat2 = param->range.parse( ptr, &ptr, rng2, NULL );
        if ( stat2 != E_STRINGPARSE_NOPARSE ) {
          if ( stat2 ) status = stat2;
          size2 = size;
          while ( isspace( *ptr ) ) ptr++;
        }
        dotdot = True;

      } else {

        /* only one dot detected */
        size1 = 0;
        stat1 = E_STRINGPARSE_NOPARSE;
        goto exit;

      }

    }

    if ( *ptr++ == ']' ) {

      if ( size1 || size2 ) {
        char *d = dst;
        if ( d != NULL ) {
          if ( size1 ) memcpy( d, rng1, size1 );
          if ( size2 ) memcpy( d + size, rng2, size2 );
        }
      }

      if ( size1 || size2 || param->range.empty ) {
        dstsize = 2 * size; 
        str = ptr;
        status = E_NONE;
      }

    }

  }

  exit:

  if ( end != NULL ) {
    *end = str;
  }

  if ( !status ) {
    param->dstsize = dstsize;
    param->range.lower = size1 ? True : False;
    param->range.dotdot = dotdot;
    param->range.upper = size2 ? True : False;
  }

  return status;

}

