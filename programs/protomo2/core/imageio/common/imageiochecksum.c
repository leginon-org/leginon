/*----------------------------------------------------------------------------*
*
*  imageiochecksum.c  -  imageio: image files
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
#include "imageiochecksum.h"
#include "fileiochecksum.h"
#include "exception.h"


/* functions */

extern Status ImageioChecksum
              (const Imageio *imageio,
               ChecksumType type,
               Size buflen,
               uint8_t *buf)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return exception( E_IMAGEIO );

  status = FileioChecksum( imageio->fileio, type, buflen, buf );
  if ( exception( status ) ) return status;

  return E_NONE;

}
