/*----------------------------------------------------------------------------*
*
*  fffioget.c  -  imageio: FFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fffio.h"
#include "imageiocommon.h"
#include "stringparse.h"
#include "exception.h"
#include <string.h>


/* functions */

static void FFFtoTime
            (const char ffftm[16],
             Time *tm)

{
  char buf[17];

  memcpy( buf, ffftm, 16 );
  buf[16] = 0;
  if ( StringParseDateTime( buf, NULL, tm, NULL ) ) {
    memset( tm, 0, sizeof(Time) );
  }

}


extern Status FFFGet
              (const Imageio *imageio,
               ImageioMeta *meta)

{

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  Fileio *fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_FFFIO );

  const ImageioFormat *format = imageio->format;
  if ( runcheck && ( format == NULL ) ) return pushexception( E_FFFIO );

  FFFMeta *fffmeta = imageio->meta;
  FFFHeader *hdr = &fffmeta->hdr;
  uint8_t *magic = hdr->magic;

  if ( imageio->iostat & ImageioBigNative ) {
    Size i = 0;
    if ( magic[4] != '0' ) meta->version[i++] = magic[4];
    meta->version[i++] = magic[5];
    meta->version[i++] = '.';
    if ( magic[6] != '0' ) meta->version[i++] = magic[6];
    if ( ( magic[6] != '0' ) || ( magic[7] != '0' ) ) meta->version[i++] = magic[7];
    meta->version[i] = 0;
  } else {
    Size i = 0;
    if ( magic[5] != '0' ) meta->version[i++] = magic[5];
    meta->version[i++] = magic[4];
    meta->version[i++] = '.';
    if ( magic[7] != '0' ) meta->version[i++] = magic[7];
    if ( ( magic[7] != '0' ) || ( magic[6] != '0' ) ) meta->version[i++] = magic[6];
    meta->version[i] = 0;
  }

  strncpy( meta->format, format->version.ident, sizeof( meta->format ) );

  FFFtoTime( hdr->cre, &meta->cre );
  FFFtoTime( hdr->mod, &meta->mod );

  return E_NONE;

}
