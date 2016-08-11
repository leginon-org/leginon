/*----------------------------------------------------------------------------*
*
*  suprimiofmt.c  -  imageio: suprim files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "suprimio.h"
#include "imageiocommon.h"
#include "exception.h"


/* macros */

#define MAXSIZE   0x0fffffff
#define COUNTMAX  300


/* functions */

static Status SuprimFmtCheckTrace
              (Fileio *fileio)

{
  Size offs = SuprimTraceOffs;
  int32_t nr, len;
  Status status;

  do {

    status = FileioRead( fileio, offs, sizeof(int32_t), &nr );
    if ( exception( status) ) return status;
    offs += sizeof(int32_t);
    if ( !nr ) break;
    if ( ( nr < 0 ) || ( nr > COUNTMAX ) ) return exception( E_SUPRIMIO_TRC );
    nr += 2;

    while ( nr-- ) {
      status = FileioRead( fileio, offs, sizeof(int32_t), &len );
      if ( exception( status) ) return status;
      offs += sizeof(int32_t) + len;
      if ( ( len < 0 ) || ( offs >= SuprimHeaderSize ) ) return exception( E_SUPRIMIO_TRC );
    }

  } while ( True );

  return E_NONE;

}


static Status SuprimFmtCheck
              (SuprimHeader *hdr,
               Fileio *fileio)

{
  static const char SuprimHeaderTsize[9] = { 0, 1, 2, 0, 4, 0, 0, 0, 8 };

  if ( ( hdr->nrow <= 0 ) || ( hdr->nrow > MAXSIZE ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->ncol <= 0 ) || ( hdr->ncol > MAXSIZE ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->reg[NSLICES].l < 0 ) || ( hdr->reg[NSLICES].l > MAXSIZE ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->format < 0 ) || ( hdr->format > 8 ) || !SuprimHeaderTsize[hdr->format] ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->intern < 0 ) || ( hdr->intern >= SuprimTypeMax ) ) return E_IMAGEIO_FORMAT;

  return SuprimFmtCheckTrace( fileio );

}


extern Status SuprimFmt
              (Imageio *imageio)

{
  Fileio *fileio;
  SuprimHeader hdr;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_SUPRIMIO );
  if ( runcheck && ( FileioGetMode( fileio ) & IOCre ) ) return pushexception( E_SUPRIMIO );

  /* read header in native byte order and check */
  ImageioSetEndian( &imageio->iostat, ~ImageioByteSwap );
  status = SuprimHeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = SuprimFmtCheck( &hdr, fileio );
  if ( !status ) return E_NONE;

  /* non-native check */
  ImageioSetEndian( &imageio->iostat, ImageioByteSwap );
  status = SuprimHeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = SuprimFmtCheck( &hdr, fileio );
  if ( !status ) return E_NONE;

  /* checks failed */
  pushexception( status );

  return status;

}
