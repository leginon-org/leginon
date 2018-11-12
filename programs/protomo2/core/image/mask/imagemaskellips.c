/*----------------------------------------------------------------------------*
*
*  imagemaskellips.c  -  image: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagemaskcommon.h"
#include "exception.h"


/* functions */

extern Status ImageMaskEllips
              (const Image *image,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param)

{
  Coord bbuf[3];
  MaskParam par;
  Status status;

  if ( argcheck( image == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( param == NULL ) ) return exception( E_ARGVAL );

  status = ImageMaskSetParam( image, param, &par, bbuf, sizeof(bbuf) );
  if ( exception( status ) ) return status;

  status = MaskEllips( image->dim, image->len, image->type, addr, A, b, &par );
  if ( exception( status ) ) return status;

  return E_NONE;

}
