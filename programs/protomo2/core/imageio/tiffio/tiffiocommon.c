/*----------------------------------------------------------------------------*
*
*  tiffiocommon.c  -  imageio: TIFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tiffiocommon.h"
#include "imageiocommon.h"
#include "exception.h"


/* functions */

extern void TiffioError
            (const char* module,
             const char* fmt,
             va_list ap)

{
  char msg[128];

  pushexception( E_TIFFIO_ERR );
  vsnprintf( msg, 128, fmt, ap );
  appendexception( msg );

}


extern Status TiffioOpen
              (Imageio *imageio)

{
  const char *path;
  int fd;
  char mode[] = { 0, 'm', 0 }; /* disable memory mapping */
  char *dummy = mode;
  TIFF *handle;
  TiffioMeta *meta;
  Status status;

  if ( imageio->iostat & ImageioModeCre ) {
    mode[0] = 'w';
  } else {
    if ( imageio->iostat & ImageioModeWr ) {
      mode[0] = 'a';
    } else {
      mode[0] = 'r';
    }
  }
  if ( mode[0] == 'a' ) {
    return pushexception( E_IMAGEIO_IOP );
  }

  /* bug fix, TIFFFdOpen does not read from the beginning of the file! */
  status = FileioRead( imageio->fileio, 0, 0, dummy );
  if ( exception( status ) ) return status;
  /* end bug fix */

  path = FileioGetPath( imageio->fileio );
  fd = FileioGetFd( imageio->fileio );
  handle = TIFFFdOpen( fd, path, mode );
  if ( handle == NULL ) {
    return exception( E_TIFFIO_ERR );
  }
  meta = imageio->meta;
  meta->handle = handle;

  return E_NONE;

}


extern void TiffSignConvert
              (Type type,
               void *buf,
               Size len)

{

  switch ( type ) {
    case TypeUint8:
    case TypeInt8: {
      uint8_t *dst = buf;
      while ( len-- ) {
        *dst++ ^= UINT8_C( 0x80 );
      }
      break;
    }
    case TypeUint16:
    case TypeInt16: {
      uint16_t *dst=buf;
      while ( len-- ) {
        *dst++ ^= UINT16_C( 0x8000 );
      }
      break;
    }
    case TypeUint32:
    case TypeInt32: {
      uint32_t *dst=buf;
      while ( len-- ) {
        *dst++ ^= UINT32_C( 0x80000000 );
      }
      break;
    }
    case TypeUint64:
    case TypeInt64: {
      uint64_t *dst=buf;
      while ( len-- ) {
        *dst++ ^= UINT64_C( 0x8000000000000000 );
      }
      break;
    }
    default: break;
  }

}
