/*----------------------------------------------------------------------------*
*
*  histogram.c  -  array: statistics
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

extern Status Histogram
              (Type type,
               Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher)

{
  Status status;

  if ( src   == NULL ) return exception( E_ARGVAL );
  if ( histo == NULL ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeUint8:  status = HistogramUint8 ( count, src, min, step, n, histo, lower, higher ); break;
    case TypeUint16: status = HistogramUint16( count, src, min, step, n, histo, lower, higher ); break;
    case TypeUint32: status = HistogramUint32( count, src, min, step, n, histo, lower, higher ); break;
    case TypeInt8:   status = HistogramInt8  ( count, src, min, step, n, histo, lower, higher ); break;
    case TypeInt16:  status = HistogramInt16 ( count, src, min, step, n, histo, lower, higher ); break;
    case TypeInt32:  status = HistogramInt32 ( count, src, min, step, n, histo, lower, higher ); break;
    case TypeReal:   status = HistogramReal  ( count, src, min, step, n, histo, lower, higher ); break;
    case TypeImag:   status = HistogramImag  ( count, src, min, step, n, histo, lower, higher ); break;
    default:         status = exception( E_STATISTICS_DATATYPE );
  }

  return status;

}
