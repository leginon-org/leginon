/*----------------------------------------------------------------------------*
*
*  tomoiocommon.c  -  core: tomography
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
#include "baselib.h"
#include "strings.h"
#include "exception.h"
#include "macros.h"


/* functions */

extern char *TomoioPath
             (const char *path,
              const char *prfx,
              const char *sffx)

{

  if ( ( path == NULL ) || !*path ) {
    if ( ( prfx == NULL ) || !*prfx ) {
      pushexception( E_TOMOIO ); return NULL;
    }
    path = prfx;
  } else {
    sffx = NULL;
  }

  return StringConcat( prfx, sffx, NULL );

}


extern Status TomoioSetOffset
              (Tomoio *tomoio,
               Offset offset)

{

  if ( tomoio == NULL ) return E_ARGVAL;
  if ( offset < 0 ) return E_ARGVAL;

  tomoio->offs = offset;

  return E_NONE;

}


extern Status TomoioGetOffset
              (Tomoio *tomoio)

{
  Offset newoffs;
  Status status;

  if ( tomoio == NULL ) return exception( E_ARGVAL );

  if ( ~tomoio->mode & IOExt ) return E_EOF;

  I3Image *i3image = tomoio->metadata;
  Size count = i3image->len[3];
  if ( count >= (Size)OffsetMaxSize ) return exception( E_INTOVFL );

  Size size = i3image->size * i3image->elsize;
  if ( size >= (Size)OffsetMaxSize ) return exception( E_INTOVFL );

  status = MulOffset( count, size, &newoffs );
  if ( exception( status ) ) return status;

  switch ( tomoio->mode ) {

    case TomoioModeImageio: {
      Imageio *imageio = tomoio->handle.imageio;
      status = ImageioResize( imageio, count + 1 );
      if ( popexception( status ) ) return status;
      break;
    }

    default: return exception( E_TOMOIO );

  }

  tomoio->offs = newoffs;

  return E_NONE;

}


extern Status TomoioSetSize
              (Tomoio *tomoio)

{
  Offset newoffs;
  Status status;

  if ( tomoio == NULL ) return exception( E_ARGVAL );

  I3Image *i3image = tomoio->metadata;
  Size count = i3image->len[3];
  if ( count >= (Size)OffsetMaxSize ) return exception( E_INTOVFL );

  Size size = i3image->size * i3image->elsize;
  if ( size >= (Size)OffsetMaxSize ) return exception( E_INTOVFL );

  status = MulOffset( count, size, &newoffs );
  if ( exception( status ) ) return status;

  if ( newoffs != tomoio->offs ) return exception( E_TOMOIO );

  i3image->len[3] = count + 1;

  return E_NONE;

}


extern Status TomoioGetCount
              (Tomoio *tomoio,
               Size *count)

{

  if ( argcheck( tomoio == NULL ) ) return exception( E_ARGVAL );

  I3Image *i3image = tomoio->metadata;
  if ( count != NULL ) *count = i3image->len[3];

  return E_NONE;

}
