/*----------------------------------------------------------------------------*
*
*  imageiodel.c  -  imageio: image files
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

extern Status ImageioDel
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );

  status = FileioSetMode( imageio->fileio, IODel );
  if ( pushexception( status ) ) return status;

  imageio->iostat |= ImageioModeDel;

  return E_NONE;

}


extern Status ImageioUndel
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );

  status = FileioClearMode( imageio->fileio, IODel );
  if ( pushexception( status ) ) return status;

  imageio->iostat &= ~ImageioModeDel;

  return E_NONE;

}
