/*----------------------------------------------------------------------------*
*
*  tiffiowr.c  -  imageio: TIFF files
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
#include "baselib.h"


/* functions */

extern Status TiffioWr
              (Imageio *imageio,
               Offset offset,
               Size length,
               const void *addr)

{
  Size nxe, nx;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeWr ) ) return pushexception( E_TIFFIO );

  TiffioMeta *meta = imageio->meta;
  if ( runcheck && ( meta == NULL ) ) return pushexception( E_TIFFIO );

  TIFF *handle = meta->handle;
  if ( runcheck && ( handle == NULL ) ) return pushexception( E_TIFFIO );

  if ( meta->flags & TIFFIO_TRNSP ) {
    nx = imageio->len[1];
  } else {
    nx = imageio->len[0];
  }
  nxe = nx * TypeGetSize( imageio->eltype );

  if ( meta->flags & TIFFIO_TILED ) {

    status = pushexception( E_TIFFIO );

  } else {

    if ( offset % nxe ) return pushexception( E_TIFFIO );
    if ( length % nxe ) return pushexception( E_TIFFIO );

    offset /= nxe;
    length /= nxe;

    const uint8_t *src = addr;

    for ( Size i = 0; i < length; i++, offset++, src += nxe ) {

      if ( TIFFWriteScanline( handle, (tdata_t)src, offset, 0 ) != 1 ) {
        return exception( E_TIFFIO_ERR );
      }

    }

    meta->mod = TimeGet();
    meta->flags |= TIFFIO_WR | TIFFIO_MOD;
    status = E_NONE;

  }

  return status;

}
