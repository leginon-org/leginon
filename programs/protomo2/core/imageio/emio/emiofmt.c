/*----------------------------------------------------------------------------*
*
*  emiofmt.c  -  imageio: em files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "emio.h"
#include "imageiocommon.h"
#include "exception.h"
#include "baselib.h"


/* functions */

static Status EMFmtCheck
              (EMHeader *hdr,
               Imageio *imageio)

{
  Type type;
  Offset size, filesize;

  if ( hdr->machine  >= EMmachinemax  ) return E_IMAGEIO_FORMAT;
  if ( hdr->datatype >= EMdatatypemax ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->nx <= 0 ) || ( hdr->ny <= 0 ) || ( hdr->nz <= 0 ) ) return E_IMAGEIO_FORMAT;

  switch ( hdr->datatype ) {
    case EMbyte:   type = TypeUint8;   break;
    case EMint16:  type = TypeInt16;   break;
    case EMint32:  type = TypeInt32;   break;
    case EMfloat:  type = TypeReal32;  break;
    case EMcmplx:  type = TypeCmplx32; break;
    case EMdouble: type = TypeReal64;  break;
    default: return E_IMAGEIO_FMTERR;
  }
  size = hdr->nx; size *= TypeGetSize( type );
  filesize = hdr->ny; filesize *= hdr->nz;
  if ( MulOffset( size, filesize, &filesize ) ) {
    return E_IMAGEIO_FORMAT;
  }
  filesize += EMHeaderSize;
  if ( filesize < EMHeaderSize ) {
    return E_IMAGEIO_FORMAT;
  }

  /* allow padding to 1024 byte blocks */
  size = FileioGetSize( imageio->fileio );
  if ( ( filesize < size ) || ( filesize > size + 1024 ) ) {
    return E_IMAGEIO_FORMAT;
  }
  if ( imageio->iostat & ImageioFmtAuto ) {
    ImageioStatus e;
    switch ( hdr->machine ) {
      case EMVAX:
      case EMPC:  e = 0; break;
      case EMSGI:
      case EMMAC: e = ImageioBigFile; break;
      default:    e = imageio->iostat & ImageioBigFile;
    }
    if ( e ^ ( imageio->iostat & ImageioBigFile ) ) return E_IMAGEIO_FORMAT;
    if ( ( hdr->nx & 0xffff0000 ) || ( hdr->ny & 0xffff0000 ) || ( hdr->nz & 0xffff0000 ) ) return E_IMAGEIO_FORMAT;
  }

  return E_NONE;

}


extern Status EMFmt
              (Imageio *imageio)

{
  Fileio *fileio;
  EMHeader hdr;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_EMIO );
  if ( runcheck && ( FileioGetMode( fileio ) & IOCre ) ) return pushexception( E_EMIO );

  /* read header in native byte order and check */
  ImageioSetEndian( &imageio->iostat, ~ImageioByteSwap );
  status = EMHeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = EMFmtCheck( &hdr, imageio );
  if ( !status ) return E_NONE;

  /* non-native check */
  ImageioSetEndian( &imageio->iostat, ImageioByteSwap );
  status = EMHeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = EMFmtCheck( &hdr, imageio );
  if ( !status ) return E_NONE;

  /* checks failed */
  pushexception( status );

  return status;

}
