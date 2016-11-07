/*----------------------------------------------------------------------------*
*
*  minmaxmeanint32.c  -  array: statistics
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

extern Status MinmaxmeanInt32
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param)

{
  StatFlags flags;

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  flags = ( param == NULL ) ? StatAll : param->flags;

  statfloat( int32_t, INT32_MIN, INT32_MAX );

  return E_NONE;

}
