/*----------------------------------------------------------------------------*
*
*  ccp4iosiz.c  -  imageio: CCP4 files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "ccp4io.h"
#include "imageiodefault.h"
#include "exception.h"


/* functions */

extern Status CCP4Siz
              (Imageio *imageio,
               Offset size,
               Size length)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  status = ImageioSiz( imageio, size, length );
  if (exception( status ) ) return status;

  CCP4Meta *meta = imageio->meta;
  CCP4Header *hdr = &meta->header;
  Size dim = imageio->dim;

  if ( dim == 1 ) {
    hdr->nx = hdr->mx = length;
    hdr->a  = hdr->mx; 
  } else if ( dim == 2 ) {
    hdr->ny = hdr->my = length;
    hdr->b  = hdr->my; 
  } else if ( dim == 3 ) {
    hdr->nz = hdr->mz = length;
    hdr->c  = hdr->mz; 
  } else {
    return pushexception( E_IMAGEIO_DIM );
  }

  return E_NONE;

}
