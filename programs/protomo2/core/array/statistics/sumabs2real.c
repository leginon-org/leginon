/*----------------------------------------------------------------------------*
*
*  sumabs2real.c  -  array: calculate sum of squared absolute value
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

extern Status Sumabs2Real
              (Size size,
               const void *src,
               void *dst)

{

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  const Real *s = src;
  Real *d = dst;

  Real sum2 = 0;
  s += size;
  while ( s-- != src ) {
    sum2 += *s * *s;
  }
  *d = sum2;

  return E_NONE;

}
