/*----------------------------------------------------------------------------*
*
*  stringformatuint64.c  -  core: character string operations
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

extern char *StringFormatUint64
             (uint64_t src,
              uint64_t base,
              Size *dstlen,
              char *dst)

{
  Size len = *dstlen;
  char *ptr = dst;

  if ( ( base < 2 ) || ( base > 62 ) ) return NULL;
  if ( !len-- ) return NULL;

  do {
    uint64_t rem = src % base;
    if ( rem < 10 ) {
      rem += '0';
    } else if ( rem < 36 ) {
      rem += 'A' - 10;
    } else {
      rem += 'a' - 36;
    }
    if ( !len-- ) return NULL;
    *ptr++ = rem;
    src /= base;
  } while ( src );
  *ptr-- = 0;

  for ( char *p = dst; p < ptr; p++, ptr-- ) {
    char c = *p;
    *p = *ptr;
    *ptr = c;
  }

  *dstlen = len + 1;

  return dst;

}
