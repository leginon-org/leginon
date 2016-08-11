/*----------------------------------------------------------------------------*
*
*  mask_real.c  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mask.h"
#include "exception.h"


/* functions */

extern Status MaskReal
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param)

{
  Status status = E_NONE;

  while ( !status ) {

    switch ( param->flags & MaskFunctionMask ) {

      case MaskFunctionNone:   return E_NONE;
      case MaskFunctionRect:   status = MaskRectReal( dim, len, addr, A, b, param ); break;
      case MaskFunctionEllips: status = MaskEllipsReal( dim, len, addr, A, b, param ); break;
      case MaskFunctionGauss:  status = MaskGaussReal( dim, len, addr, A, b, param ); break;
      case MaskFunctionWedge:  status = MaskWedgeReal( dim, len, addr, A, b, param ); break;
      default: status = exception( E_MASK_FUNC );

    }

    param++;

  }

  return status;

}
