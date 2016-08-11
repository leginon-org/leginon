/*----------------------------------------------------------------------------*
*
*  imagicioget.c  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagicio.h"
#include "imageiocommon.h"
#include "exception.h"
#include <string.h>


/* functions */

extern Status ImagicGet
              (const Imageio *imageio,
               ImageioMeta *meta)

{
  const ImageioFormat *format;
  ImagicMeta *imagicmeta;
  Fileio *fileio;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_IMAGICIO );

  format = imageio->format;
  if ( runcheck && ( format == NULL ) ) return pushexception( E_IMAGICIO );

  imagicmeta = imageio->meta;
  if ( runcheck && ( imagicmeta == NULL ) ) return pushexception( E_IMAGICIO );

  strncpy( meta->format, imageio->format->version.ident, sizeof( meta->format ) );

  meta->cre = imagicmeta->cre;

  return E_NONE;

}
