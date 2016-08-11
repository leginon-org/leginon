/*----------------------------------------------------------------------------*
*
*  convol.c  -  array: convolution type filters
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

extern Status Convol2d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeUint8:  status = exception( Convol2dUint8 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeUint16: status = exception( Convol2dUint16( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeUint32: status = exception( Convol2dUint32( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt8:   status = exception( Convol2dInt8  ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt16:  status = exception( Convol2dInt16 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt32:  status = exception( Convol2dInt32 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeReal:   status = exception( Convol2dReal  ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    default:         status = exception( E_CONVOL_TYPE );
  }

  return status;

}


extern Status Convol3d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr)

{
  Status status;

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeUint8:  status = exception( Convol3dUint8 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeUint16: status = exception( Convol3dUint16( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeUint32: status = exception( Convol3dUint32( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt8:   status = exception( Convol3dInt8  ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt16:  status = exception( Convol3dInt16 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeInt32:  status = exception( Convol3dInt32 ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    case TypeReal:   status = exception( Convol3dReal  ( srclen, srcaddr, krnlen, krnaddr, dstaddr ) ); break;
    default:         status = exception( E_CONVOL_TYPE );
  }

  return status;

}
