/*----------------------------------------------------------------------------*
*
*  imageiostd.c  -  imageio: image files
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

extern Status ImageioStd
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );

  if ( imageio->iocap || ( ~imageio->cap & ImageioCapStd ) ) {
    return pushexception( E_IMAGEIO );
  }

  imageio->iocap = 0;

  status = FileioStd( imageio->fileio );
  if ( !exception( status ) ) {
    imageio->iocap = ImageioCapStd;
  }

  return E_NONE;

}
