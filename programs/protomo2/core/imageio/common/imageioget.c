/*----------------------------------------------------------------------------*
*
*  imageioget.c  -  imageio: image files
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
#include <string.h>


/* functions */

extern const char *ImageioGetPath
                   (const Imageio *imageio)

{

  if ( imageio == NULL ) return NULL;

  if ( imageio->fileio == NULL ) return NULL;

  const char *path = FileioGetFullPath( imageio->fileio );

  return path;

}


extern IOMode ImageioGetMode
              (const Imageio *imageio)

{

  if ( imageio == NULL ) return 0;

  IOMode mode = FileioGetMode( imageio->fileio );

  return mode;

}


extern Status ImageioGetMeta
              (const Imageio *imageio,
               ImageioMeta *meta)

{
  Status status;

  if ( meta == NULL ) return pushexception( E_ARGVAL );
  memset( meta, 0, sizeof(ImageioMeta) );

  if ( imageio == NULL ) return pushexception( E_ARGVAL );
  if ( ~imageio->iostat & ImageioModeOpen ) return pushexception( E_IMAGEIO );

  meta->endian = ( imageio->iostat & ImageioBigFile ) ? 'B' : 'L';

  meta->cap = imageio->iocap;

  meta->mode = imageio->iostat & ImageioModeMask;

  if ( ( imageio->format == NULL ) || ( imageio->format->get == NULL ) ) {
    status = pushexception( E_IMAGEIO );
  } else {
    status = imageio->format->get( imageio, meta );
    logexception( status );
  }

  return status;

}


extern Size ImageioGetDim
            (const Imageio *imageio)

{

  if ( imageio == NULL ) return 0;

  return imageio->dim;

}


extern const Size *ImageioGetLen
                   (const Imageio *imageio)

{

  if ( imageio == NULL ) return NULL;

  return imageio->len;

}


extern const Index *ImageioGetLow
                    (const Imageio *imageio)

{

  if ( imageio == NULL ) return NULL;

  return imageio->low;

}


extern Type ImageioGetType
            (const Imageio *imageio)

{

  if ( imageio == NULL ) return 0;

  return imageio->eltype;

}


extern ImageAttr ImageioGetAttr
                 (const Imageio *imageio)

{

  if ( imageio == NULL ) return 0;

  return imageio->attr;

}
