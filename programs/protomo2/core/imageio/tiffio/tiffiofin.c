/*----------------------------------------------------------------------------*
*
*  tiffiofin.c  -  imageio: TIFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tiffiocommon.h"
#include "imageiocommon.h"
#include "exception.h"
#include <stdlib.h>
#include <sys/stat.h>


/* functions */

extern Status TiffioFin
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioFinClose ) ) return pushexception( E_TIFFIO );

  TiffioMeta *meta = imageio->meta;
  if ( runcheck && ( meta == NULL ) ) return pushexception( E_TIFFIO );

  TIFF *handle = meta->handle;
  if ( runcheck && ( handle == NULL ) ) return pushexception( E_TIFFIO );

  switch ( imageio->iocap ) {

    case ImageioCapLib: {
      break;
    }

    case ImageioCapAmap: {
      status = ImageioAmapFinal( imageio );
      if ( exception( status ) ) return status;
      break;
    }

    default: {
      return pushexception( E_TIFFIO );
    }

  }

  Fileio *fileio = imageio->fileio;

  if ( imageio->iostat & ImageioModeCre ) {
    if ( imageio->iostat & ImageioModeDel ) {
      status = FileioUnlink( fileio );
      if ( pushexception( status ) ) return status;
    } else {
      status = FileioSetFileMode( fileio );
      if ( pushexception( status ) ) return status;
    }
  }

  TIFFClose( handle );
  meta->handle = NULL;

  FileioDestroy( fileio );

  imageio->fileio = NULL;

  return E_NONE;

}
