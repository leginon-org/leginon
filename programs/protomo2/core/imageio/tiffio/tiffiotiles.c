/*----------------------------------------------------------------------------*
*
*  tiffiotiles.c  -  imageio: TIFF files
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

extern Status TiffioLoadTiles
              (Imageio *imageio,
               void *buf)

{
  TiffioMeta *meta = imageio->meta;
  TIFF *handle = meta->handle;
  Status status;

  uint32_t nx = imageio->len[0];
  uint32_t ny = imageio->len[1];
  Size tsize = TypeGetSize( imageio->eltype );

  uint32_t tx = meta->tags.tilewidth;
  uint32_t ty = meta->tags.tilelength;
  if ( ( tx == 0 ) || ( ty == 0 ) ) {
    return pushexception( E_TIFFIO );
  }

  uint8_t *ptr = buf;
  for ( uint32_t iy = 0; iy < ny; iy += ty ) {
    for ( uint32_t ix = 0; ix < nx; ix += tx ) {
      uint32_t nxt = nx - ix;
      if ( nxt > tx ) nxt = tx;
      tsize_t stat = TIFFReadTile( handle, imageio->buf, ix, iy, 0, 0 );
      if ( ( stat < 0 ) || ( (uint32_t)stat != tx * ty * tsize ) ) {
        return exception( E_TIFFIO_ERR );
      }
      meta->flags |= TIFFIO_RD;
      if ( meta->flags & TIFFIO_SMP_SGN ) {
        TiffSignConvert( imageio->eltype, imageio->buf, tx * ty );
      }
      uint8_t *tile = imageio->buf;
      for ( uint32_t jy = iy; ( jy < ( iy + ty ) ) && ( jy < ny ); jy++ ) {
        uint32_t y0;
        if ( imageio->iostat & ImageioBlkFlipY ) {
          y0 = ny - 1 - jy;
        } else {
          y0 = jy;
        }
        if ( imageio->iostat & ImageioBlkFlipX ) {
          uint8_t *tmp = ptr + ( nx - 1 - ix + nx * y0 ) * tsize;
          memcpy( tmp, tile, nxt * tsize );
          status = ImageioFlip( nxt, tsize, tmp );
          if ( pushexception( status ) ) return status;
        } else {
          memcpy( ptr + ( ix + nx * y0 ) * tsize, tile, nxt * tsize );
        }
        tile += tx * tsize;
      } /* end for jy */
    } /* end for ix */
  } /* end for iy */

  return E_NONE;

}
