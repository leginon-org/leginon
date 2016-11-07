/*----------------------------------------------------------------------------*
*
*  mask_rect_real.c  -  array: mask operations
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
#include "matn.h"
#include "exception.h"


/* functions */

extern Status MaskRectReal
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param)

{
  Coord Abuf[3*3], bbuf[3];
  Status status;

  if ( argcheck( len == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( param == NULL ) ) return exception( E_ARGVAL );

  if ( A == NULL ) {
    A = param->A;
  } else if ( param->A != NULL ) {
    MatnMul( dim, A, param->A, Abuf );
    A = Abuf;
  }
  if ( b == NULL ) {
    b = param->b;
  } else if ( param->b != NULL ) {
    for ( Size d = 0; d < dim; d++ ) {
      bbuf[d] = b[d] + param->b[d];
    }
    b = bbuf;
  }

  MaskFlags flags = ( param->flags & ~MaskFunctionMask ) | MaskFunctionRect;

  Coord val = ( param->flags & MaskModeVal ) ? param->val : 0;

  if ( flags & MaskModeAuto ) {

    Stat stat;
    switch ( dim ) {
      case 2: status = MaskStatRect2dReal( len, addr, A, b, param->wid, &stat, flags ); break;
      case 3: status = MaskStatRect3dReal( len, addr, A, b, param->wid, &stat, flags ); break;
      default: status = exception( E_MASK_DIM );
    }
    if ( exception( status ) ) return status;
    val = stat.mean;

  }

  if ( ( param->apo == NULL ) || ( ~flags & MaskModeApod ) ) {

    switch ( dim ) {
      case 2: status = MaskRect2dReal( len, addr, A, b, param->wid, val, flags ); break;
      case 3: status = MaskRect3dReal( len, addr, A, b, param->wid, val, flags ); break;
      default: status = exception( E_MASK_DIM );
    }

  } else {

    flags |= MaskModeApod;

    switch ( dim ) {
      case 2: status = MaskRectApod2dReal( len, addr, A, b, param->wid, param->apo, val, flags ); break;
      case 3: status = MaskRectApod3dReal( len, addr, A, b, param->wid, param->apo, val, flags ); break;
      default: status = exception( E_MASK_DIM );
    }

  }

  return status;

}
