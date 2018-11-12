/*----------------------------------------------------------------------------*
*
*  minmaxmeanuint8.c  -  array: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "minmaxmean.h"
#include "exception.h"


/* functions */

extern Status MinmaxmeanUint8
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param)

{
  StatFlags flags;

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  flags = ( param == NULL ) ? StatAll : param->flags;

  statfloat( uint8_t, 0, UINT8_MAX );

  return E_NONE;

}
