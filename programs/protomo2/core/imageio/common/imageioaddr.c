/*----------------------------------------------------------------------------*
*
*  imageioaddr.c  -  imageio: image files
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
#include "baselib.h"
#include "exception.h"


/* functions */

extern Status ImageioAddr
              (Imageio *imageio,
               Offset offset,
               Size length,
               void **addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) )  return pushexception( E_ARGVAL );
  if ( argcheck( offset < 0 ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset  < 0 ) ) return pushexception( E_IMAGEIO );

  if ( ~imageio->iostat & ImageioModeOpen ) {
    return pushexception( E_IMAGEIO );
  }

  if ( imageio->iocap & ( ImageioCapMmap | ImageioCapAmap ) ) {

    if ( imageio->iostat & ImageioModeLd ) {

      switch ( imageio->iocap ) {
        case ImageioCapMmap: {
          if ( imageio->format->adr == NULL ) return pushexception( E_IMAGEIO );
          status = imageio->format->adr(  imageio, offset, length, addr );
          if ( exception( status ) ) return status;
          break;
        }
        case ImageioCapAmap: {
          status = ImageioAmapAddr( imageio, offset, length, addr );
          if ( pushexception( status ) ) return status;
          break;
        }
        default: return pushexception( E_IMAGEIO );
      }

    } else if ( imageio->iocap == ImageioCapMmap ) {

      status = ImageioMmapSet( imageio, offset, length, addr );
      if ( pushexception( status ) ) return status;

    } else {

      return pushexception( E_IMAGEIO );

    }

    if ( imageio->iostat & ImageioModeWr ) {
      imageio->iostat |= ImageioModData | ImageioFinMod;
    }

  } else {

    *addr = NULL;

  }

  return E_NONE;

}
