/*----------------------------------------------------------------------------*
*
*  imageioread.c  -  imageio: image files
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

extern Status ImageioRead
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr)

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

  if ( ~imageio->iostat & ImageioModeRd ) {
    return pushexception( E_IMAGEIO_RD );
  }

  if ( imageio->rd == NULL ) {
    return pushexception( E_IMAGEIO_IOP );
  }

  if ( !length ) return E_NONE;

  status = ImageioSizeSet( imageio, &offset, length, &size, &count );
  if ( pushexception( status ) ) return status;

  if ( count ) {

    status = ImageioRdBlock( imageio, imageio->rd, offset, size, count, addr );
    if ( exception( status ) ) return status;

  } else {

    status = imageio->rd( imageio, offset, size, addr );
    if ( exception( status ) ) return status;

    if ( imageio->cvtcount && ( imageio->rdcvt != NULL ) ) {
      imageio->rdcvt( imageio->cvtcount * length, addr, addr );
    }

  }

  return E_NONE;

}
