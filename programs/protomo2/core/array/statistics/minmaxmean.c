/*----------------------------------------------------------------------------*
*
*  minmaxmean.c  -  array: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "statistics.h"
#include "exception.h"


/* functions */

extern Status Minmaxmean
              (Type type,
               Size count,
               const void *src,
               Stat *dst,
               const StatParam *param)

{
  Status status;

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeUint8:  status = MinmaxmeanUint8 ( count, src, dst, param ); break;
    case TypeUint16: status = MinmaxmeanUint16( count, src, dst, param ); break;
    case TypeUint32: status = MinmaxmeanUint32( count, src, dst, param ); break;
    case TypeInt8:   status = MinmaxmeanInt8  ( count, src, dst, param ); break;
    case TypeInt16:  status = MinmaxmeanInt16 ( count, src, dst, param ); break;
    case TypeInt32:  status = MinmaxmeanInt32 ( count, src, dst, param ); break;
    case TypeReal:   status = MinmaxmeanReal  ( count, src, dst, param ); break;
    case TypeImag:   status = MinmaxmeanImag  ( count, src, dst, param ); break;
    case TypeCmplx:  status = MinmaxmeanCmplx ( count, src, dst, param ); break;
    default:         status = exception( E_STATISTICS_DATATYPE );
  }

  return status;

}
