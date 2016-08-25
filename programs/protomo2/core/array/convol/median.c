/*----------------------------------------------------------------------------*
*
*  median.c  -  array: convolution type filters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "convol.h"
#include "exception.h"


/* functions */

extern Status FilterMedian2d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeUint8:  status = exception( FilterMedian2dUint8 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeUint16: status = exception( FilterMedian2dUint16( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeUint32: status = exception( FilterMedian2dUint32( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt8:   status = exception( FilterMedian2dInt8  ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt16:  status = exception( FilterMedian2dInt16 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt32:  status = exception( FilterMedian2dInt32 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeReal:   status = exception( FilterMedian2dReal  ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    default:         status = exception( E_CONVOL_TYPE );
  }

  return status;

}


extern Status FilterMedian3d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeUint8:  status = exception( FilterMedian3dUint8 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeUint16: status = exception( FilterMedian3dUint16( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeUint32: status = exception( FilterMedian3dUint32( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt8:   status = exception( FilterMedian3dInt8  ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt16:  status = exception( FilterMedian3dInt16 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt32:  status = exception( FilterMedian3dInt32 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeReal:   status = exception( FilterMedian3dReal  ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    default:         status = exception( E_CONVOL_TYPE );
  }

  return status;

}
