/*----------------------------------------------------------------------------*
*
*  imageioopen.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageioformat.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

static Imageio *ImageioOpen
               (const char *path,
                Image *image,
                IOMode mode,
                const ImageioParam *param)

{
  const char *errpath;
  Status status;

  if ( argcheck( path == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  if ( mode & ( IOCre | IONew ) ) {
    pushexception( E_ARGVAL ); return NULL;
  }

  if ( param == NULL ) param = &ImageioParamDefault;

  Imageio *imageio = malloc( sizeof(Imageio) );
  if ( imageio == NULL ) {
    pushexception( E_MALLOC ); goto error1;
  }
  *imageio = ImageioInitializer;

  FileioParam fileioparam = FileioParamInitializer;
  fileioparam.mode = mode;
  fileioparam.filepath = param->filepath;

  Fileio *fileio = FileioOpen( path, &fileioparam );
  if ( testcondition( fileio == NULL ) ) goto error2;
  imageio->fileio = fileio;

  mode = FileioGetMode( fileio );
  if ( mode & IORd  ) imageio->iostat |= ImageioModeRd;
  if ( mode & IOWr  ) imageio->iostat |= ImageioModeWr;

  imageio->iostat |= ImageioGetEndian();

  status = ImageioFormatOld( param, imageio );
  if ( exception( status ) ) goto error3;

  imageio->iostat |= ImageioModeFmt;

  imageio->offset = OffsetMax;

  imageio->cap = param->cap & ( imageio->format->cap | ImageioCapAuto );

  if ( imageio->format->old == NULL ) {
    pushexception( E_IMAGEIO ); goto error3;
  }
  status = imageio->format->old( imageio );
  if ( exception( status ) ) goto error3;

  if ( image != NULL ) {
    image->dim = imageio->dim;
    image->len = imageio->len;
    image->low = imageio->low;
    image->type = imageio->eltype;
    image->attr = imageio->attr;
  }

  imageio->iostat |= ImageioModeOpen;

  return imageio;

  error3:
  errpath = FileioGetPath( fileio );
  if ( errpath == NULL ) errpath = path;
  appendexception( ", file " );
  appendexception( errpath );
  status = FileioClose( fileio );
  logexception( status );
  logexception( E_IMAGEIO_FIN );

  error2:
  ImageioCleanup( imageio );

  return NULL;

  error1:
  appendexception( ", " );
  appendexception( path );

  return NULL;

}


extern Imageio *ImageioOpenReadOnly
               (const char *path,
                Image *image,
                const ImageioParam *param)

{

  return ImageioOpen( path, image, IORd, param );

}


extern Imageio *ImageioOpenReadWrite
               (const char *path,
                Image *image,
                const ImageioParam *param)

{

  return ImageioOpen( path, image, IORd | IOWr, param );

}
