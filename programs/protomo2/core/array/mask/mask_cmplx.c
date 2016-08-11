/*----------------------------------------------------------------------------*
*
*  mask_cmplx.c  -  array: mask operations
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

extern Status MaskCmplx
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
      case MaskFunctionRect:   status = MaskRectCmplx( dim, len, addr, A, b, param ); break;
      case MaskFunctionEllips: status = MaskEllipsCmplx( dim, len, addr, A, b, param ); break;
      case MaskFunctionGauss:  status = MaskGaussCmplx( dim, len, addr, A, b, param ); break;
      case MaskFunctionWedge:  status = MaskWedgeCmplx( dim, len, addr, A, b, param ); break;
      default: status = exception( E_MASK_FUNC );

    }

    param++;

  }

  return status;

}
