/*----------------------------------------------------------------------------*
*
*  mask.c  -  array: mask operations
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

extern Status Mask
              (Size dim,
               const Size *len,
               Type type,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param)

{
  Status status = E_NONE;

  while ( !status ) {

    switch ( param->flags & MaskFunctionMask ) {

      case MaskFunctionNone:   return E_NONE;
      case MaskFunctionRect:   status = MaskRect( dim, len, type, addr, A, b, param ); break;
      case MaskFunctionEllips: status = MaskEllips( dim, len, type, addr, A, b, param ); break;
      case MaskFunctionGauss:  status = MaskGauss( dim, len, type, addr, A, b, param ); break;
      case MaskFunctionWedge:  status = MaskWedge( dim, len, type, addr, A, b, param ); break;
      default: status = exception( E_MASK_FUNC );

    }

    param++;

  }

  return status;

}
