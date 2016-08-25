/*----------------------------------------------------------------------------*
*
*  stringformatdatetime.c  -  core: character string operations
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
#include "exception.h"
#include <string.h>


/* functions */

extern char *StringFormatDateTime
             (const Time *tm,
              const char sep[5],
              Size *dstlen,
              char *dst)

{
  char dsep='.', fsep=' ', tsep=':', xsep='.';
  int xdig = 2;
  uint32_t td, tt;
  unsigned char c0, c1, c2, c3, c4, c5, c6, c7, c8;

  if ( sep != NULL ) {
    dsep = sep[0];
    fsep = sep[1];
    tsep = sep[2];
    xsep = sep[3];
    xdig = sep[4] - '0';
    if ( xdig <= 0 ) xsep = 0;
  }

  td = tm->date;
  c0 = td & 0x0f; td >>= 4;
  c1 = td & 0x0f; td >>= 4;
  c2 = td & 0x0f; td >>= 4;
  c3 = td & 0x0f; td >>= 4;
  c4 = td & 0x0f; td >>= 4;
  c5 = td & 0x0f; td >>= 4;
  c6 = td & 0x0f; td >>= 4;
  c7 = td & 0x0f; td >>= 4;

  if ( *dstlen ) { *dst++ = c7 + '0'; (*dstlen)--; } else return dst;
  if ( *dstlen ) { *dst++ = c6 + '0'; (*dstlen)--; } else return dst;
  if ( *dstlen ) { *dst++ = c5 + '0'; (*dstlen)--; } else return dst;
  if ( *dstlen ) { *dst++ = c4 + '0'; (*dstlen)--; } else return dst;
  if ( dsep ) {
    if ( *dstlen ) { *dst++ = dsep; (*dstlen)--; } else return dst;
  }
  if ( *dstlen ) { *dst++ = c3 + '0'; (*dstlen)--; } else return dst;
  if ( *dstlen ) { *dst++ = c2 + '0'; (*dstlen)--; } else return dst;
  if ( dsep) {
    if ( *dstlen ) { *dst++ = dsep; (*dstlen)--; } else return dst;
  }
  if ( *dstlen ) { *dst++ = c1 + '0'; (*dstlen)--; } else return dst;
  if ( *dstlen ) { *dst++ = c0 + '0'; (*dstlen)--; } else return dst;
  if ( fsep ) {
    if ( *dstlen ) { *dst++ = fsep; (*dstlen)--; } else return dst;
  }

  tt = tm->time;
  c0 = tt % 10; tt /= 10;
  c1 = tt % 10; tt /= 10;
  c2 = tt % 10; tt /= 10;
  c3 = tt % 60; tt /= 60;
  c4 = c3 / 10; c3 %= 10;
  c5 = tt % 60; tt /= 60;
  c6 = c5 / 10; c5 %= 10;
  c7 = tt % 24; tt /= 24;
  c8 = c7 / 10; c7 %= 10;

  if ( *dstlen ) { *dst++ = c8 + '0'; (*dstlen)--; } else return dst;
  if ( *dstlen ) { *dst++ = c7 + '0'; (*dstlen)--; } else return dst;
  if ( tsep) {
    if ( *dstlen ) { *dst++ = tsep; (*dstlen)--; } else return dst;
  }
  if ( *dstlen ) { *dst++ = c6 + '0'; (*dstlen)--; } else return dst;
  if ( *dstlen ) { *dst++ = c5 + '0'; (*dstlen)--; } else return dst;
  if ( tsep ) {
    if ( *dstlen ) { *dst++ = tsep; (*dstlen)--; } else return dst;
  }
  if ( *dstlen ) { *dst++ = c4 + '0'; (*dstlen)--; } else return dst;
  if ( *dstlen ) { *dst++ = c3 + '0'; (*dstlen)--; } else return dst;
  if (xsep) {
    if ( *dstlen ) { *dst++ = xsep; (*dstlen)--; } else return dst;
  }
  if ( xdig > 0 ) {
    if ( xdig >= 1 ) { if ( *dstlen ) { *dst++ = c2 + '0'; (*dstlen)--; } else return dst; }
    if ( xdig >= 2 ) { if ( *dstlen ) { *dst++ = c1 + '0'; (*dstlen)--; } else return dst; }
    if ( xdig >= 3 ) { if ( *dstlen ) { *dst++ = c0 + '0'; (*dstlen)--; } else return dst; }
  }

  if ( *dstlen ) {
    *dst = 0;
  }

  return dst;

}
