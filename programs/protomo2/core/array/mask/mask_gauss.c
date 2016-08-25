/*----------------------------------------------------------------------------*
*
*  mask_gauss.c  -  array: mask operations
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
#include "mathdefs.h"
#include "exception.h"


/* functions */

extern Status MaskGauss
              (Size dim,
               const Size *len,
               Type type,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param)

{
  Status status;

  if ( argcheck( len == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( param == NULL ) ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeReal:  status = exception( MaskGaussReal( dim, len, addr, A, b, param ) ); break;
    case TypeCmplx: status = exception( MaskGaussCmplx( dim, len, addr, A, b, param ) ); break;
    default: status = exception( E_MASK_TYPE );
  }

  return status;

}
