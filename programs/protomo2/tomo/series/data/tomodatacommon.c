/*----------------------------------------------------------------------------*
*
*  tomodatacommon.c  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomodata.h"
#include "stringformat.h"
#include "exception.h"
#include <stdio.h>
#include <string.h>


/* variables */

static const char *fmt1 = "[%"SizeU"]";
static const char *fmt2 = " image %-3"SizeU" ";
static const char *fmt3 = "image %"SizeU" ";


/* functions */

extern void TomodataLogString
            (const Tomodata *data,
             const TomodataDscr *dscr,
             Size index,
             char *buf,
             Size buflen)

{
  char hdr[64];

  if ( buflen ) *buf = 0;
  if ( buflen < 2 ) return;
  buflen -= 2;

  sprintf( hdr, fmt1, data->images );
  Size len1 = strlen( hdr );

  char *ptr = buf;
  Size len = buflen;

  sprintf( hdr, fmt1, index );
  ptr = StringFormatString( 0, hdr, &buflen, ptr );
  len -= buflen;
  while ( buflen && ( len < len1 ) ) {
    *ptr++ = ' '; len++; buflen--;
  }

  dscr += index;

  sprintf( hdr, fmt2, dscr->number );
  ptr = StringFormatString( 0, hdr, &buflen, ptr );

  const TomofileDscr *file = data->file->dscr;
  const char *name = data->file->string;
  if ( file != NULL ) name += file[data->image[index].fileindex].nameindex;

  len = buflen;
  ptr = StringFormatString( 0, name, &buflen, ptr );
  len -= buflen;
  *ptr++ = ':';
  while ( buflen && ( len < (Size)data->file->width ) ) {
    *ptr++ = ' '; len++; buflen--;
  }
  *ptr = 0;

}


extern void TomodataErrString
            (const TomodataDscr *dscr,
             Size index,
             char *buf,
             Size buflen)

{
  char str[64];

  if ( buflen ) *buf = 0;
  if ( buflen < 2 ) return;
  buflen -= 2;

  sprintf( str, fmt3, dscr[index].number );
  buf = StringFormatString( 0, str, &buflen, buf );

  sprintf( str, fmt1, index );
  buf = StringFormatString( 0, str, &buflen, buf );

  *buf = 0;

}
