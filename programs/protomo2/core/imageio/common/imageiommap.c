/*----------------------------------------------------------------------------*
*
*  imageiommap.c  -  imageio: image files
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

extern Status ImageioMmapSet
              (Imageio *imageio,
               Offset offset,
               Size length,
               void **addr)

{
  Size size;
  Status status;

  if ( argcheck( imageio == NULL ) ) return exception( E_ARGVAL );
  if ( offset < 0 ) return exception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return exception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset < 0 ) ) return exception( E_IMAGEIO );

  status = ImageioSizeSet( imageio, &offset, length, &size, NULL );
  if ( exception( status ) ) return status;

  status = FileioMap( imageio->fileio, offset, size );
  if ( exception( status ) ) return status;

  if ( addr != NULL ) {
    *addr = FileioGetAddr( imageio->fileio );
    if ( *addr == NULL ) return exception( E_IMAGEIO );
  }

  return E_NONE;

}


extern Status ImageioMmap
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset  < 0 ) ) return pushexception( E_IMAGEIO );

  if ( ( imageio->iocap && ( imageio->iocap != ImageioCapMmap ) ) || ( ~imageio->cap & ImageioCapMmap ) ) {
    return pushexception( E_IMAGEIO );
  }

  imageio->iocap = 0;

  Size elsize = TypeGetSize( imageio->eltype );
  if ( OffsetMax <= IndexMax ) {
    if ( (Size)imageio->arrsize > SizeMax / elsize ) {
      status = exception( E_IMAGEIO_BIG ); return E_NONE;
    }
  } else {
    if ( imageio->arrsize > (Offset)( SizeMax / elsize ) ) {
      status = exception( E_IMAGEIO_BIG ); return E_NONE;
    }
  }

  status = ImageioMmapSet( imageio, 0, imageio->arrsize, NULL );
  if ( !exception( status ) ) {
    imageio->iocap = ImageioCapMmap;
  }

  return E_NONE;

}
