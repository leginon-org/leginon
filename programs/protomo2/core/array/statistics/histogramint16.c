/*----------------------------------------------------------------------------*
*
*  histogramint16.c  -  array: statistics
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
#include <string.h>


/* functions */

extern Status HistogramInt16
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

  if ( n ) memset( histo, 0, n * sizeof(Size) );
  if ( lower  != NULL) *lower  = 0;
  if ( higher != NULL) *higher = 0;

  ihisto( int16_t );

  return E_NONE;

}
