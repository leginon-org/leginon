/*----------------------------------------------------------------------------*
*
*  suprimioget.c  -  imageio: suprim files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "suprimio.h"
#include "imageiocommon.h"
#include "exception.h"
#include <string.h>


/* functions */

extern Status SuprimGet
              (const Imageio *imageio,
               ImageioMeta *meta)

{
  const ImageioFormat *format;
  Fileio *fileio;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_SUPRIMIO );

  format = imageio->format;
  if ( runcheck && ( format == NULL ) ) return pushexception( E_SUPRIMIO );

  strncpy( meta->format, imageio->format->version.ident, sizeof( meta->format ) );

  return E_NONE;

}
