/*----------------------------------------------------------------------------*
*
*  imageioout.c  -  imageio: image files
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

extern Status ImageioOut
              (const char *path,
               const Image *image,
               const void *addr,
               const ImageioParam *param)

{
  ImageioParam ioparam;
  Offset arrsize;
  Status status;

  if ( param == NULL ) {
    ioparam = ImageioParamDefault;
    ioparam.cap = ImageioCapUnix | ImageioCapLib;
  } else {
    ioparam = *param;
  }
  ioparam.mode |= ImageioModeDel;

  Imageio *imageio = ImageioCreate( path, image, &ioparam );
  status = testcondition( imageio == NULL );
  if ( status ) return status;

  status = MulOffset( imageio->arrsize, TypeGetSize( imageio->eltype ), &arrsize );
  if ( status || ( arrsize > OffsetMaxSize ) ) {
    status = pushexception( E_IMAGEIO_BIG ); goto error;
  }

  status = ImageioWrite( imageio, 0, imageio->arrsize, addr );
  if ( exception( status ) ) goto error;

  status = ImageioUndel( imageio );
  if ( exception( status ) ) goto error;

  status = ImageioClose( imageio );
  logexception( status );

  return status;

  error: ImageioClose( imageio );

  return status;

}
