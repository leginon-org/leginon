/*----------------------------------------------------------------------------*
*
*  polar_real.c  -  array: spatial polar transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "polar.h"
#include "exception.h"


/* functions */

extern Status PolarReal
              (Size dim,
               Type type,
               const Size *srclen,
               const void *srcaddr,
               const Coord *A,
               const Coord *b,
               const Size *dstlen,
               void *dstaddr,
               const Coord *c,
               const TransformParam *param)

{
  Status status;

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstlen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( dim ) {
    case 2:  status = exception( Polar2dReal( type, srclen, srcaddr, A, b, dstlen, dstaddr, c, param ) ); break;
    case 3:  status = exception( Polar3dReal( type, srclen, srcaddr, A, b, dstlen, dstaddr, c, param ) ); break;
    default: status = exception( E_POLAR_DIM );
  }

  return status;

}
