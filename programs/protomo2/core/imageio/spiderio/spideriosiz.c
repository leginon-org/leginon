/*----------------------------------------------------------------------------*
*
*  spideriosiz.c  -  imageio: spider files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "spiderio.h"
#include "imageiodefault.h"
#include "exception.h"


/* functions */

extern Status SpiderSiz
              (Imageio *imageio,
               Offset size,
               Size length)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  status = ImageioSiz( imageio, size, length );
  if (exception( status ) ) return status;

  SpiderMeta *meta = imageio->meta;
  SpiderHeader *hdr = &meta->header;
  Size dim = imageio->dim;

  if ( dim == 2 ) {
    hdr->nrow = length;
  } else if ( dim == 3 ) {
    hdr->nslice = length;
  } else {
    return pushexception( E_IMAGEIO_DIM );
  }

  return E_NONE;

}
