/*----------------------------------------------------------------------------*
*
*  imageiomode.c  -  imageio: image files
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
#include "exception.h"


/* functions */

extern Status ImageioModeInit
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->iocap ) ) return pushexception( E_IMAGEIO );

  ImageioCap cap = imageio->cap;
  if ( ( imageio->iostat & ImageioByteSwap ) && imageio->cvtcount ) {
    cap &= ~ImageioCapMmap;
  }

  if ( ~imageio->cap & ImageioCapAuto ) {
    switch ( imageio->cap ) {
      case ImageioCapMmap: if ( ~cap & ImageioCapMmap ) return pushexception( E_IMAGEIO_SWP );
      case ImageioCapAmap:
      case ImageioCapLoad:
      case ImageioCapStd:
      case ImageioCapUnix:
      case ImageioCapLib:  break;
      default: return pushexception( E_IMAGEIO_CAP );
    }
  }

  if ( cap & ImageioCapMmap ) {
    status = ImageioMmap( imageio );
    if ( exception( status ) ) return status;
    if ( imageio->iocap == ImageioCapMmap ) return E_NONE;
  }

  if ( ( imageio->cap & ImageioCapMmap ) && ( cap & ImageioCapLoad ) ) {
    status = ImageioAmap( imageio );
    if ( exception( status ) ) return status;
    if ( imageio->iocap == ImageioCapAmap ) return E_NONE;
    cap &= ~( ImageioCapAmap | ImageioCapLoad );
  }

  if ( cap & ( ImageioCapAmap | ImageioCapLoad ) ) {
    status = ImageioAmap( imageio );
    if ( exception( status ) ) return status;
    if ( imageio->iocap == ImageioCapAmap ) return E_NONE;
  }

  if ( cap & ImageioCapStd ) {
    status = ImageioStd( imageio );
    if ( exception( status ) ) return status;
    if ( imageio->iocap == ImageioCapStd ) return E_NONE;
  }

  if ( cap & ImageioCapUnix ) {
    imageio->iocap = ImageioCapUnix;
    return E_NONE;
  }

  if ( cap & ImageioCapLib ) {
    imageio->iocap = ImageioCapLib;
    return E_NONE;
  }

  return pushexception( E_IMAGEIO_CAP );

}
