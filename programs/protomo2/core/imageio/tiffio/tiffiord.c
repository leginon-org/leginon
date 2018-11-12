/*----------------------------------------------------------------------------*
*
*  tiffiord.c  -  imageio: TIFF files
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
#include <string.h>  


/* functions */

extern Status TiffioRd
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr)

{
  Size nxe, nx, ny;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeRd ) ) return pushexception( E_TIFFIO );

  TiffioMeta *meta = imageio->meta;
  if ( runcheck && ( meta == NULL ) ) return pushexception( E_TIFFIO );

  TIFF *handle = meta->handle;
  if ( runcheck && ( handle == NULL ) ) return pushexception( E_TIFFIO );

  if ( meta->flags & TIFFIO_TRNSP ) {
    nx = imageio->len[1];
    ny = imageio->len[0];
  } else {
    nx = imageio->len[0];
    ny = imageio->len[1];
  }
  nxe = nx * TypeGetSize( imageio->eltype );

  if ( meta->flags & TIFFIO_TILED ) {

    if ( offset || ( length != ny * nxe ) ) {
      status = pushexception( E_TIFFIO );
    } else {
      status = TiffioLoadTiles( imageio, addr );
    }

  } else {

    if ( offset % nxe ) return pushexception( E_TIFFIO );
    if ( length % nxe ) return pushexception( E_TIFFIO );

    offset /= nxe;
    length /= nxe;

    uint8_t *dst = addr;

    for ( Size i = 0; i < length; i++, offset++, dst += nxe ) {

      if ( TIFFReadScanline( handle, dst, offset, 0 ) != 1 ) {
        return exception( E_TIFFIO_ERR );
      }

      if ( meta->flags & TIFFIO_SMP_SGN ) {
        TiffSignConvert( imageio->eltype, dst, nx );
      }

    }

    meta->flags |= TIFFIO_RD;
    status = E_NONE;

  }

  return status;

}
