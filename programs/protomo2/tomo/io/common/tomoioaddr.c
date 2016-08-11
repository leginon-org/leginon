/*----------------------------------------------------------------------------*
*
*  tomoioaddr.c  -  core: tomography
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


/* functions */

extern Status TomoioAddr
              (const Tomoio *tomoio,
               Offset offset,
               Size length,
               void **addr)

{
  Status status;

  if ( tomoio == NULL ) return exception( E_ARGVAL );
  if ( offset < 0 ) return exception( E_ARGVAL );
  if ( addr == NULL ) return exception( E_ARGVAL );

  if ( OFFSETADDOVFL( offset, tomoio->offs ) ) return exception( E_INTOVFL );
  offset += tomoio->offs;

  switch ( tomoio->mode ) {

    case TomoioModeImageio: {
      Imageio *imageio = tomoio->handle.imageio;
      I3Image *i3image = tomoio->metadata;
      Size elsize = i3image->elsize;
      status = ImageioAddr( imageio, offset / elsize, length / elsize, addr );
      if ( popexception( status ) ) return status;
      break;
    }

    case TomoioModeMalloc: {
      if ( tomoio->handle.addr == NULL ) return exception( E_TOMOIO );
      *addr = tomoio->handle.addr + offset;
      break;
    }

    default: status = exception( E_TOMOIO );

  }

  return status;

}
