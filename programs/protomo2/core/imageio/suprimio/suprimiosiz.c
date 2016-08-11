/*----------------------------------------------------------------------------*
*
*  suprimiosiz.c  -  imageio: suprim files
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
#include "imageiodefault.h"
#include "exception.h"
#include <string.h>


/* functions */

extern Status SuprimSiz
              (Imageio *imageio,
               Offset size,
               Size length)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  status = ImageioSiz( imageio, size, length );
  if (exception( status ) ) return status;

  SuprimMeta *meta = imageio->meta;
  SuprimHeader *hdr = &meta->header;
  Size dim = imageio->dim;

  if ( dim == 2 ) {
    hdr->nrow = length;
  } else if ( dim == 3 ) {
    hdr->reg[NSLICES].l = length;
  } else {
    return pushexception( E_IMAGEIO_DIM );
  }

  return E_NONE;

}
