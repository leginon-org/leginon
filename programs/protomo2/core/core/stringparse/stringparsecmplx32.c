/*----------------------------------------------------------------------------*
*
*  stringparsecmplx32.c  -  core: character string operations
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

extern Status StringParseCmplx32
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  const char *reptr, *imptr;
  Size dstsize = 0;
  Real32 re, im;
  Status status = E_NONE;

  if ( str == NULL ) {
    if ( param == NULL ) {
      status = exception( E_ARGVAL ); goto exit;
    } else {
      dstsize = sizeof( Cmplx32 ); goto exit;
    }
  }

  status = StringParseReal32( str, &reptr, &re, param );
  if ( status ) {
    if ( status != E_STRINGPARSE_NOPARSE ) goto exit;
    re = 1;
  }

  if ( *reptr == 'i' ) {
    im = re;
    re = 0;
    str = reptr + 1;
    goto parsed;
  } else if ( status ) {
    goto exit;
  }

  if ( ( *reptr == '+' ) || ( *reptr == '-' ) ) {

    status = StringParseReal32( reptr, &imptr, &im, param );
    if ( status ) {
      if ( status != E_STRINGPARSE_NOPARSE ) goto exit;
      im = ( *imptr++ == '+' ) ? 1 : -1;
    }

    if ( *imptr == 'i' ) {
      str = imptr + 1;
      goto parsed;
    } else if ( status ) {
      goto exit;
    }

  }

  /* real */
  im = 0;
  str = reptr;

  parsed:

  if ( dst != NULL ) {
    Real32 *d = dst;
    d[0] = re;
    d[1] = im;
  }
  dstsize = sizeof( Cmplx32 );
  status = E_NONE;

  exit:

  if ( end != NULL ) {
    *end = str;
  }

  if ( param != NULL ) {
    param->dstsize = dstsize;
  }

  return status;

}
