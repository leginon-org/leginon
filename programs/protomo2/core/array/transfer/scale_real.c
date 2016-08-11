/*----------------------------------------------------------------------------*
*
*  scale_real.c  -  array: pixel value transfer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transfer.h"
#include "exception.h"


/* functions */

extern Status ScaleReal
              (Type type,
               Size count,
               const void *src,
               void *dst,
               const TransferParam *param)

{
  Status status;

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeUint8:  status = ScaleUint8Real ( count, src, dst, param ); break;
    case TypeUint16: status = ScaleUint16Real( count, src, dst, param ); break;
    case TypeUint32: status = ScaleUint32Real( count, src, dst, param ); break;
    case TypeInt8:   status = ScaleInt8Real  ( count, src, dst, param ); break;
    case TypeInt16:  status = ScaleInt16Real ( count, src, dst, param ); break;
    case TypeInt32:  status = ScaleInt32Real ( count, src, dst, param ); break;
    case TypeReal:   status = ScaleRealReal  ( count, src, dst, param ); break;
    default:         status = exception( E_TRANSFER_DATATYPE );
  }

  return status;

}
