/*----------------------------------------------------------------------------*
*
*  tomoioread.c  -  core: tomography
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
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomoioRead
              (const Tomoio *tomoio,
               Offset offset,
               Size length,
               void *buf)

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
        status = ImageioRead( imageio, offset / elsize, length / elsize, buf );
        if ( popexception( status ) ) return status;
      } else {
        char *addr = tomoio->addr;
        memcpy( buf, addr + offset, length );
      }
      break;
    }

    case TomoioModeMalloc: {
      if ( tomoio->handle.addr == NULL ) return exception( E_TOMOIO );
      if ( length ) {
        memcpy( buf, tomoio->handle.addr + offset, length );
      }
      break;
    }

    default: status = exception( E_TOMOIO );

  }

  return status;

}


extern Status TomoioReadBuf
              (const Tomoio *tomoio,
               Offset offset,
               Size length,
               void **buf)

{
  void *rdbuf = NULL;
  Status status = E_NONE;

  if ( tomoio == NULL ) return exception( E_ARGVAL );
  if ( offset < 0 ) return exception( E_ARGVAL );
  if ( buf == NULL ) return exception( E_ARGVAL );

  if ( OFFSETADDOVFL( offset, tomoio->offs ) ) return exception( E_INTOVFL );
  offset += tomoio->offs;

  switch ( tomoio->mode ) {

    case TomoioModeImageio: {
      if ( length ) {
        Imageio *imageio = tomoio->handle.imageio;
        I3Image *i3image = tomoio->metadata;
        rdbuf = malloc( length );
        if ( rdbuf == NULL ) return exception( E_MALLOC );
        if ( tomoio->addr == NULL ) {
          Size elsize = i3image->elsize;
          status = ImageioRead( imageio, offset / elsize, length / elsize, rdbuf );
          if ( popexception( status ) ) goto error;
        } else {
          char *addr = tomoio->addr;
          memcpy( rdbuf, addr + offset, length );
        }
      }
      break;
    }

    case TomoioModeMalloc: {
      if ( tomoio->handle.addr == NULL ) return exception( E_TOMOIO );
      if ( length ) {
        rdbuf = malloc( length );
        if ( rdbuf == NULL ) return exception( E_MALLOC );
        memcpy( rdbuf, tomoio->handle.addr + offset, length );
      }
      break;
    }

    default: return exception( E_TOMOIO );

  }

  *buf = rdbuf;

  return E_NONE;

  error: free( rdbuf );

  return status;

}
