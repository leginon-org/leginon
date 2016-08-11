/*----------------------------------------------------------------------------*
*
*  imageiowrite.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageiocommon.h"
#include "imageioblock.h"
#include "exception.h"


/* functions */

extern Status ImageioWrite
              (Imageio *imageio,
               Offset offset,
               Size length,
               const void *addr)

{
  Size size, count;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( offset < 0 ) return pushexception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset  < 0 ) ) return pushexception( E_IMAGEIO );

  if ( ~imageio->iostat & ImageioModeOpen ) {
    return pushexception( E_IMAGEIO );
  }

  if ( ~imageio->iostat & ImageioModeWr ) {
    return pushexception( E_IMAGEIO_WR );
  }

  if ( imageio->wr == NULL ) {
    return pushexception( E_IMAGEIO_IOP );
  }

  if ( !length ) return E_NONE;

  status = ImageioSizeSet( imageio, &offset, length, &size, &count );
  if ( pushexception( status ) ) return status;

  if ( count ) {

    status = ImageioWrBlock( imageio, imageio->wr, offset, size, count, addr );
    if ( exception( status ) ) return status;

  } else {

    if ( imageio->cvtcount && ( imageio->wrcvt != NULL ) ) {
      status = ImageioBufAlloc( imageio, size );
      if ( pushexception( status ) ) return status;
      imageio->wrcvt( imageio->cvtcount * length, addr, imageio->buf );
      addr = imageio->buf;
    }

    status = imageio->wr( imageio, offset, size, addr );
    if ( exception( status ) ) return status;
  }

  imageio->iostat |= ImageioModData | ImageioFinMod;

  return E_NONE;

}
