/*----------------------------------------------------------------------------*
*
*  imagiciofmt.c  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagicio.h"
#include "imagicioconfig.h"
#include "imageiocommon.h"
#include "exception.h"


/* functions */

static Status ImagicFmtCheck
              (ImagicHeader *hdr,
               const Imageio *imageio)

{
  const char *ident = imageio->format->version.ident;
  ImageioStatus iostat = imageio->iostat;

  if ( hdr->imn  < 1 ) return E_IMAGEIO_FORMAT;
  if ( hdr->ifol < 0 ) return E_IMAGEIO_FORMAT;
  if ( hdr->nblocks != 1 ) return E_IMAGEIO_FORMAT;
  if ( hdr->rsize < 0 ) return E_IMAGEIO_FORMAT;
  if ( hdr->ixlp < 0 ) return E_IMAGEIO_FORMAT;
  if ( hdr->iylp < 0 ) return E_IMAGEIO_FORMAT;
  if ( hdr->izlp < 0 ) return E_IMAGEIO_FORMAT;
  if ( hdr->i4lp < 0 ) return E_IMAGEIO_FORMAT;
  if ( hdr->i5lp < 0 ) return E_IMAGEIO_FORMAT;
  if ( hdr->i6lp < 0 ) return E_IMAGEIO_FORMAT;

  if ( ( hdr->nday   < 1 ) || ( hdr->nday   > 31 ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->nmonth < 1 ) || ( hdr->nmonth > 31 ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->nyear  < 1 ) || ( hdr->nyear  > 2099 ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->nhour  < 0 ) || ( hdr->nhour  > 23 ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->nminut < 0 ) || ( hdr->nminut > 59 ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->nsec   < 0 ) || ( hdr->nsec   > 59 ) ) return E_IMAGEIO_FORMAT;

  if ( hdr->imavers < 19800000 ) return E_IMAGEIO_FORMAT;
  if ( hdr->imavers > 20999999 ) return E_IMAGEIO_FORMAT;

  if ( iostat & ImageioFmtAuto ) {

    switch ( hdr->realtype ) {
      case 0x04040404: {
        /* big endian, IEEE float */
        if ( ~iostat & ImageioBigNative ) return E_IMAGEIO_FORMAT;
        break;
      }
      case 0x02020202: {
        /* little endian, IEEE float */
        if ( iostat & ImageioBigNative ) return E_IMAGEIO_FORMAT;
        break;
      }
      case 0x01000000: {
        /* DEC/VAX float */
        return E_IMAGICIO_FLOAT;
      }
      default: return E_IMAGEIO_FORMAT;
    }

  }

  if ( ident[6] ) {
    if ( *((int32_t *)&hdr->user1) != IMAGICUSER1 ) return E_IMAGEIO_FORMAT;
    if ( *((int32_t *)&hdr->user2) != IMAGICUSER2RAW ) return E_IMAGEIO_FORMAT;
    if ( hdr->ierror != IMAGICUSER2RAW ) return E_IMAGEIO_FORMAT;
  }

  if ( ImagicGetType( hdr, NULL, NULL ) ) return E_IMAGEIO_FORMAT;

  return E_NONE;

}


extern Status ImagicFmt
              (Imageio *imageio)

{
  Fileio *fileio;
  ImagicHeader hdr;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_IMAGICIO );
  if ( runcheck && ( FileioGetMode( fileio ) & IOCre ) ) return pushexception( E_IMAGICIO );

  /* read header in native byte order and check */
  ImageioSetEndian( &imageio->iostat, ~ImageioByteSwap );
  status = ImagicHeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = ImagicFmtCheck( &hdr, imageio );
  if ( !status ) return E_NONE;

  /* non-native check */
  ImageioSetEndian( &imageio->iostat, ImageioByteSwap );
  status = ImagicHeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = ImagicFmtCheck( &hdr, imageio );
  if ( !status ) return E_NONE;

  /* checks failed */
  pushexception( status );

  return status;

}
