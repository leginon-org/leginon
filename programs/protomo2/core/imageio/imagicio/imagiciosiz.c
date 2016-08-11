/*----------------------------------------------------------------------------*
*
*  imagiciosiz.c  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagicio.h"
#include "imageiodefault.h"
#include "array.h"
#include "exception.h"


/* functions */

extern Status ImagicSiz
              (Imageio *imageio,
               Offset size,
               Size length)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( length > INT32_MAX ) return pushexception( E_INTOVFL );

  status = ImageioSiz( imageio, size, length );
  if (exception( status ) ) return status;

  ImagicMeta *meta = imageio->meta;
  ImagicHeader *hdr = &meta->header;
  Size dim = imageio->dim;

  if ( dim == 1 ) {

    if ( imageio->format->version.ident[6] ) {
      hdr->iylp = length;
    } else {
      hdr->ixlp = length;
    }
    hdr->rsize = length;

  } else if ( dim == 2 ) {

    if ( imageio->format->version.ident[6] ) {
      hdr->ixlp = length;
    } else {
      hdr->iylp = length;
    }
    hdr->rsize = length * imageio->len[0];

  } else if ( dim == 3 ) {

    hdr->izlp = length;
    hdr->rsize = length * imageio->len[1] * imageio->len[0];

  } else {

    hdr->ifol = length * imageio->len[2] - 1;
    hdr->i4lp = length;
    hdr->rsize = imageio->len[2] * imageio->len[1] * imageio->len[0];
    if ( imageio->iostat & ImageioModeCre ) {
      meta->ifol = hdr->ifol;
    }

  }

  return E_NONE;

}
