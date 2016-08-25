/*----------------------------------------------------------------------------*
*
*  imageioresize.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageiodefault.h"
#include "array.h"
#include "baselib.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status ImageioResize
              (Imageio *imageio,
               Size length)

{
  Offset arrsize;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset  < 0 ) ) return pushexception( E_IMAGEIO );

  if ( ~imageio->iostat & ImageioModeOpen ) {
    return pushexception( E_IMAGEIO );
  }

  if ( ~imageio->iostat & ImageioModeCre ) {
    return pushexception( E_IMAGEIO_SZ );
  }

  if ( ~imageio->iostat & ImageioModeWr ) {
    return pushexception( E_IMAGEIO_WR );
  }

  if ( imageio->format->siz == NULL ) {
    return pushexception( E_IMAGEIO_IOP );
  }

  if ( !imageio->dim ) return E_NONE;
  Size dim = imageio->dim - 1;
  Size len = imageio->len[dim];

  if ( length == len ) {

    status = ImageioSiz( imageio, imageio->arrsize, length );
    if ( exception( status ) ) return status;

  } else {

    imageio->len[dim] = length;
    status = ArrayOffset( dim, imageio->len, TypeGetSize( imageio->eltype ), &arrsize );
    if ( status ) {
      imageio->len[dim] = len;
      return pushexception( E_IMAGEIO_BIG );
    }

    status = imageio->format->siz( imageio, arrsize, length );
    if ( exception( status ) ) return status;

    imageio->arrsize = arrsize;

    imageio->iostat |= ImageioModMeta | ImageioModData | ImageioFinMod;

  }

  return E_NONE;

}
