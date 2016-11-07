/*----------------------------------------------------------------------------*
*
*  stringformatstring.c  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "stringformat.h"


/* functions */

extern char *StringFormatString
             (Size srclen,
              const char *src,
              Size *dstlen,
              char *dst)

{

  if ( srclen ) {

    while ( srclen && *src && *dstlen ) {
      *dst++ = *src++;
      (*dstlen)--;
      srclen--;
    }

  } else {

    while ( *src && *dstlen ) {
      *dst++ = *src++;
      (*dstlen)--;
    }

  }

  if ( *dstlen ) {
    *dst = 0;
  }

  return dst;

}
