/*----------------------------------------------------------------------------*
*
*  tomoiowrite.c  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoiocommon.h"
#include "exception.h"
#include "macros.h"
#include <string.h>


/* functions */

extern Status TomoioWrite
              (const Tomoio *tomoio,
               Offset offset,
               Size length,
               const void *buf)

{
  Status status = E_NONE;

  if ( tomoio == NULL ) return exception( E_ARGVAL );
  if ( offset < 0 ) return exception( E_ARGVAL );
  if ( buf == NULL ) return exception( E_ARGVAL );

  if ( OFFSETADDOVFL( offset, tomoio->offs ) ) return exception( E_INTOVFL );
  offset += tomoio->offs;

  switch ( tomoio->mode ) {

    case TomoioModeImageio: {
      Imageio *imageio = tomoio->handle.imageio;
      I3Image *i3image = tomoio->metadata;
      if ( tomoio->addr == NULL ) {
        Size elsize = i3image->elsize;
        status = ImageioWrite( imageio, offset / elsize, length / elsize, buf );
        if ( popexception( status ) ) return status;
      } else {
        char *addr = tomoio->addr;
        memcpy( addr + offset, buf, length );
      }
      break;
    }

    case TomoioModeMalloc: {
      if ( tomoio->handle.addr == NULL ) return exception( E_TOMOIO );
      if ( length ) {
        memcpy( tomoio->handle.addr + offset, buf, length );
      }
      break;
    }

    default: status = exception( E_TOMOIO );

  }

  return status;

}
