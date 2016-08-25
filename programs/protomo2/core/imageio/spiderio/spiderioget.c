/*----------------------------------------------------------------------------*
*
*  spiderioget.c  -  imageio: spider files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "spiderio.h"
#include "imageiocommon.h"
#include "exception.h"
#include <string.h>


/* functions */

extern Status SpiderGet
              (const Imageio *imageio,
               ImageioMeta *meta)

{
  const ImageioFormat *format;
  SpiderMeta *spidermeta;
  Fileio *fileio;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_SPIDERIO );

  format = imageio->format;
  if ( runcheck && ( format == NULL ) ) return pushexception( E_SPIDERIO );

  spidermeta = imageio->meta;
  if ( runcheck && ( spidermeta == NULL ) ) return pushexception( E_SPIDERIO );

  strncpy( meta->format, imageio->format->version.ident, sizeof( meta->format ) );

  meta->cre = spidermeta->cre;

  return E_NONE;

}
