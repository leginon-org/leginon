/*----------------------------------------------------------------------------*
*
*  imagemask.c  -  image: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagemask.h"
#include "exception.h"


/* functions */

extern Status ImageMask
              (const Image *image,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param)

{
  Status status = E_NONE;

  while ( !status ) {

    switch ( param->flags & MaskFunctionMask ) {

      case MaskFunctionNone:   return E_NONE;
      case MaskFunctionRect:   status = ImageMaskRect( image, addr, A, b, param ); break;
      case MaskFunctionEllips: status = ImageMaskEllips( image, addr, A, b, param ); break;
      case MaskFunctionGauss:  status = ImageMaskGauss( image, addr, A, b, param ); break;
      case MaskFunctionWedge:  status = ImageMaskWedge( image, addr, A, b, param ); break;
      default: status = exception( E_IMAGEMASK_FUNC );

    }

    param++;

  }

  return status;

}
