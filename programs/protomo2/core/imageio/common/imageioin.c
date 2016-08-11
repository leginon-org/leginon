/*----------------------------------------------------------------------------*
*
*  imageioin.c  -  imageio: image files
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
#include <stdlib.h>


/* functions */

extern void *ImageioIn
             (const char *path,
              Image *image,
              const ImageioParam *param)

{
  ImageioParam ioparam;
  Image src, dst = ImageInitializer;
  Offset arrsize;
  Status status;

  if ( param == NULL ) {
    ioparam = ImageioParamDefault;
  } else {
    ioparam = *param;
    ioparam.cap &= ~ImageioCapAll;
  }
  ioparam.cap = ImageioCapUnix | ImageioCapLib;

  Imageio *imageio = ImageioOpenReadOnly( path, &src, &ioparam );
  if ( testcondition( imageio == NULL ) ) return NULL;

  status = MulOffset( imageio->arrsize, TypeGetSize( imageio->eltype ), &arrsize );
  if ( status || ( arrsize > OffsetMaxSize ) ) {
    pushexception( E_IMAGEIO_BIG ); goto error1;
  }

  if ( image != NULL ) {
    status = ImageMetaCopyAlloc( &src, &dst, 0 );
    if ( pushexception( status ) ) goto error1;
  }

  void *addr = malloc( arrsize );
  if ( addr == NULL ) {
    pushexception( E_MALLOC ); goto error2;
  }

  status = ImageioRead( imageio, 0, imageio->arrsize, addr );
  if ( exception( status ) ) goto error3;

  status = ImageioClose( imageio );
  if ( exception( status ) ) goto error3;

  if ( image != NULL ) {
    *image = dst;
  }

  return addr;

  error3: free( addr );
  error2: if ( dst.len != NULL ) free( dst.len );
          if ( dst.low != NULL ) free( dst.low );
  error1: ImageioClose( imageio );

  return NULL;

}
