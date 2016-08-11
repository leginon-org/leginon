/*----------------------------------------------------------------------------*
*
*  tiffiosyn.c  -  imageio: TIFF files
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
#include "stringformat.h"
#include "exception.h"


/* functions */

extern Status TiffioSyn
              (Imageio *imageio)

{
  uint32_t nx, ny;
  char buf[32];
  Size len;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeWr ) ) return pushexception( E_TIFFIO );

  TiffioMeta *meta = imageio->meta;
  if ( runcheck && ( meta == NULL ) ) return pushexception( E_TIFFIO );

  TIFF *handle = meta->handle;
  if ( runcheck && ( handle == NULL ) ) return pushexception( E_TIFFIO );

  if ( ~meta->flags & TIFFIO_INIT ) {

    if ( meta->flags & TIFFIO_TRNSP ) {
      nx = imageio->len[1];
      ny = imageio->len[0];
    } else {
      nx = imageio->len[0];
      ny = imageio->len[1];
    }
    if ( TIFFSetField( handle, TIFFTAG_IMAGEWIDTH,  nx ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_IMAGELENGTH, ny ) != 1 ) return E_TIFFIO_ERR;

    /* tags sorted by code */
    if ( TIFFSetField( handle, TIFFTAG_BITSPERSAMPLE,   meta->tags.sampsiz[0]     ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_COMPRESSION,     meta->tags.compression    ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_PHOTOMETRIC,     meta->tags.photometric    ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_ORIENTATION,     meta->tags.orientation    ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_SAMPLESPERPIXEL, meta->tags.sampnum        ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_ROWSPERSTRIP,    meta->tags.rowsperstrip   ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_XRESOLUTION,     meta->tags.xresolution    ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_YRESOLUTION,     meta->tags.yresolution    ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_PLANARCONFIG,    meta->tags.planarconfig   ) != 1 ) return E_TIFFIO_ERR;
    if ( TIFFSetField( handle, TIFFTAG_RESOLUTIONUNIT,  meta->tags.resolutionunit ) != 1 ) return E_TIFFIO_ERR;

    if ( ~meta->flags & TIFFIO_DATE ) {

      len = sizeof( buf );
      ImageioGetVersion( NULL, TiffioVers, &len, buf );
      if ( TIFFSetField( handle, TIFFTAG_SOFTWARE, buf ) != 1 ) return E_TIFFIO_ERR;

      len = sizeof( buf );
      StringFormatDateTime( &meta->cre, ": : 0", &len, buf );
      if ( len ) {
        if ( TIFFSetField( handle, TIFFTAG_DATETIME, buf ) != 1 ) return E_TIFFIO_ERR;
      }

    }

    if ( TIFFSetField( handle, TIFFTAG_SAMPLEFORMAT, meta->tags.sampfmt ) != 1 ) return E_TIFFIO_ERR;

    meta->flags |= TIFFIO_INIT | TIFFIO_MOD;

  }

  return E_NONE;

}
