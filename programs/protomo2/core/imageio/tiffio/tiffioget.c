/*----------------------------------------------------------------------------*
*
*  tiffioget.c  -  imageio: TIFF files
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
#include <string.h>


/* functions */

extern Status TiffioGet
              (const Imageio *imageio,
               ImageioMeta *meta)

{
  const ImageioFormat *format;
  Fileio *fileio;
  TiffioMeta *tiffmeta;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_TIFFIO );

  format = imageio->format;
  if ( runcheck && ( format == NULL ) ) return pushexception( E_TIFFIO );

  tiffmeta = imageio->meta;
  if ( runcheck && ( tiffmeta == NULL ) ) return pushexception( E_TIFFIO );

  strncpy( meta->format, imageio->format->version.ident, sizeof( meta->format ) );

  meta->cre = tiffmeta->cre;
  meta->mod = tiffmeta->mod;

  return E_NONE;

}
