/*----------------------------------------------------------------------------*
*
*  min.c  -  array: convolution type filters
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

extern Status FilterMin2d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

{
  Status status;

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeUint8:  status = exception( FilterMin2dUint8 ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeUint16: status = exception( FilterMin2dUint16( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeUint32: status = exception( FilterMin2dUint32( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeInt8:   status = exception( FilterMin2dInt8  ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeInt16:  status = exception( FilterMin2dInt16 ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeInt32:  status = exception( FilterMin2dInt32 ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeReal:   status = exception( FilterMin2dReal  ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    default:         status = exception( E_CONVOL_TYPE );
  }

  return status;

}


extern Status FilterMin3d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

{
  Status status;

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeUint8:  status = exception( FilterMin3dUint8 ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeUint16: status = exception( FilterMin3dUint16( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeUint32: status = exception( FilterMin3dUint32( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeInt8:   status = exception( FilterMin3dInt8  ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeInt16:  status = exception( FilterMin3dInt16 ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeInt32:  status = exception( FilterMin3dInt32 ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    case TypeReal:   status = exception( FilterMin3dReal  ( srclen, srcaddr, krnlen, dstaddr ) ); break;
    default:         status = exception( E_CONVOL_TYPE );
  }

  return status;

}
