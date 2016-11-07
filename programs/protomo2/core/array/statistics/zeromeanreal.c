/*----------------------------------------------------------------------------*
*
*  zeromeanreal.c  -  array: set mean value to zero
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

extern Status ZeromeanReal
              (Size size,
               const void *src,
               void *dst)

{

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  const Real *s = src;
  Real *d = dst;
  Size i = 8;

  Real sum;
  Real sum0 = 0;
  Real squo = 0;
  do {
    sum = 0;
    for ( Size j = 0; j < size; j++ ) {
      sum += s[j];
    }
    Real mean = sum / size;
    for ( Size j = 0; j < size; j++ ) {
      d[j] = s[j] - mean;
    }
    if ( sum < 0 ) sum = -sum;
    if ( sum0 > 0 ) squo = sum / sum0;
    sum0 = sum;
    s = d;
  } while ( ( i-- > 0 ) && ( sum > 0 ) && ( squo < 0.1 ) );

  return E_NONE;

}
