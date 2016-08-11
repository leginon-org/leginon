/*----------------------------------------------------------------------------*
*
*  imageiocreate.c  -  imageio: image files
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

extern Imageio *ImageioCreate
               (const char *path,
                const Image *image,
                const ImageioParam *param)

{
  const char *errpath;
  Status status;

  if ( argcheck( path  == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( image == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( image->len == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  if ( param == NULL ) param = &ImageioParamDefault;

  Imageio *imageio = malloc( sizeof(Imageio) );
  if ( imageio == NULL ) {
    pushexception( E_MALLOC ); goto error1;
  }
  *imageio = ImageioInitializer;

  FileioParam fileioparam = FileioParamInitializer;
  fileioparam.mode = IOCre | IOWr | IORd;
  if ( param->mode & ImageioModeDel ) {
    fileioparam.mode |= IODel;
  }

  Fileio *fileio = FileioOpen( path, &fileioparam );
  if ( testcondition( fileio == NULL ) ) goto error2;
  imageio->fileio = fileio;

  IOMode mode = FileioGetMode( fileio );
  if ( ~mode & IOCre ) { status = pushexception( E_IMAGEIO ); goto error3; }
  imageio->iostat = ImageioModeCre;
  if ( mode & IORd  ) imageio->iostat |= ImageioModeRd;
  if ( mode & IOWr  ) imageio->iostat |= ImageioModeWr;

  /* always native byte order */
  ImageioStatus iostat = ImageioGetEndian();
  if ( iostat ) iostat |= ImageioBigFile;
  imageio->iostat |= iostat;

  const ImageioFormat *format = ImageioFormatNew( param );
  if ( testcondition( format == NULL ) ) goto error3;
  imageio->format = format;

  imageio->dim = image->dim;
  imageio->len = image->len;
  imageio->low = image->low;
  imageio->eltype = image->type;
  imageio->attr = image->attr;
  imageio->offset = OffsetMax;

  imageio->cap = param->cap & ( format->cap | ImageioCapAuto );

  if ( format->new == NULL ) {
    pushexception( E_IMAGEIO ); goto error3;
  }
  status = format->new( imageio );
  if ( exception( status ) ) goto error3;

  imageio->iostat |= ImageioModeOpen;

  return imageio;

  /* error handling */

  error3:
  errpath = FileioGetPath( fileio );
  if ( errpath == NULL ) errpath = path;
  appendexception( ", file " );
  appendexception( errpath );
  status = FileioSetMode( fileio, IODel );
  logexception( status );
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
