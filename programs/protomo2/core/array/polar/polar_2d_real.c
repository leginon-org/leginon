/*----------------------------------------------------------------------------*
*
*  polar_2d_real.c  -  array: spatial polar transformations
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

extern Status Polar2dReal
              (Type type,
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

  switch ( type ) {
    case TypeUint8:  status = exception( Polar2dUint8Real ( srclen, srcaddr, A, b, dstlen, dstaddr, c, param ) ); break;
    case TypeUint16: status = exception( Polar2dUint16Real( srclen, srcaddr, A, b, dstlen, dstaddr, c, param ) ); break;
    case TypeUint32: status = exception( Polar2dUint32Real( srclen, srcaddr, A, b, dstlen, dstaddr, c, param ) ); break;
    case TypeInt8:   status = exception( Polar2dInt8Real  ( srclen, srcaddr, A, b, dstlen, dstaddr, c, param ) ); break;
    case TypeInt16:  status = exception( Polar2dInt16Real ( srclen, srcaddr, A, b, dstlen, dstaddr, c, param ) ); break;
    case TypeInt32:  status = exception( Polar2dInt32Real ( srclen, srcaddr, A, b, dstlen, dstaddr, c, param ) ); break;
    case TypeReal:   status = exception( Polar2dRealReal  ( srclen, srcaddr, A, b, dstlen, dstaddr, c, param ) ); break;
    default:         status = exception( E_POLAR_DATATYPE );
  }

  return status;

}
