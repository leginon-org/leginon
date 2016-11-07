/*----------------------------------------------------------------------------*
*
*  emiosiz.c  -  imageio: em files
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
#include "imageiodefault.h"
#include "exception.h"


/* functions */

extern Status EMSiz
              (Imageio *imageio,
               Offset size,
               Size length)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  status = ImageioSiz( imageio, size, length );
  if (exception( status ) ) return status;

  EMMeta *meta = imageio->meta;
  EMHeader *hdr = &meta->header;
  Size dim = imageio->dim;

  if ( dim == 1 ) {
    hdr->nx = length;
  } else if ( dim == 2 ) {
    hdr->ny = length;
  } else if ( dim == 3 ) {
    hdr->nz = length;
  } else {
    return pushexception( E_IMAGEIO_DIM );
  }

  return E_NONE;

}
