/*----------------------------------------------------------------------------*
*
*  imageioclose.c  -  imageio: image files
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

extern Status ImageioClose
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->format->fin == NULL ) ) return pushexception( E_IMAGEIO );

  if ( ~imageio->iostat & ImageioModeOpen ) {
    return pushexception( E_IMAGEIO );
  }

  ImageioMode err = ImageioModeErr;
  if ( imageio->iostat & ImageioModeCre ) err |= ImageioModeDel;

  ImageioMode fin = imageio->iostat & ImageioModeDel;
  if ( fin ) fin |= err;

  imageio->iostat |= ImageioFinClose;

  if ( imageio->iostat & ImageioModeWr ) {

    if ( !fin )  {
      if ( imageio->format->fls != NULL ) {
        status = imageio->format->fls( imageio );
        if ( exception( status ) ) fin |= err;
      }
    }

    if ( !fin )  {
      if ( imageio->format->syn != NULL ) {
        status = imageio->format->syn( imageio );
        if ( exception( status ) ) fin |= err;
      }
    }

    imageio->iostat |= fin;

  } else {

    imageio->iostat &= ~ImageioModeDel;

  }

  status = imageio->format->fin( imageio );
  if ( exception( status ) ) return status;

  ImageioCleanup( imageio );

  return status;

}
