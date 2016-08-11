/*----------------------------------------------------------------------------*
*
*  histogramcalcint8.c  -  array: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "histogram.h"
#include "exception.h"


/* functions */

extern Status HistogramCalcInt8
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher)

{

  if ( src   == NULL ) return exception( E_ARGVAL );
  if ( histo == NULL ) return exception( E_ARGVAL );

  ihisto( int8_t );

  return E_NONE;

}
