/*----------------------------------------------------------------------------*
*
*  tiffiofmt.c  -  imageio: TIFF files
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

static Status TiffioFmtCheck
              (uint8_t magic[4],
               ImageioStatus iostat)

{

  if ( iostat & ImageioBigFile ) {

    if ( magic[0] != 'M' ) return E_IMAGEIO_FORMAT;
    if ( magic[1] != 'M' ) return E_IMAGEIO_FORMAT;
    if ( magic[2] !=  0  ) return E_IMAGEIO_FORMAT;
    if ( magic[3] != '*' ) return E_IMAGEIO_FORMAT;

  } else {

    if ( magic[0] != 'I' ) return E_IMAGEIO_FORMAT;
    if ( magic[1] != 'I' ) return E_IMAGEIO_FORMAT;
    if ( magic[2] != '*' ) return E_IMAGEIO_FORMAT;
    if ( magic[3] !=  0 ) return E_IMAGEIO_FORMAT;

  }

  return E_NONE;

}


extern Status TiffioFmt
              (Imageio *imageio)

{
  Fileio *fileio;
  uint8_t magic[4];
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( fileio == NULL ) return pushexception( E_TIFFIO );
  if ( runcheck && ( FileioGetMode( fileio ) & IOCre ) ) return pushexception( E_TIFFIO );

  /* read magic */
  status = FileioRead( fileio, 0, sizeof( magic ), magic );
  if ( pushexception( status ) ) return status;

  /* check in native byte order */
  ImageioSetEndian( &imageio->iostat, ~ImageioByteSwap );
  status = TiffioFmtCheck( magic, imageio->iostat );
  if ( !status ) return E_NONE;

  /* non-native check */
  ImageioSetEndian( &imageio->iostat, ImageioByteSwap );
  status = TiffioFmtCheck( magic, imageio->iostat );
  if ( !status ) return E_NONE;

  /* checks failed */
  pushexception( status );

  return status;

}
