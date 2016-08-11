/*----------------------------------------------------------------------------*
*
*  zeromeancmplx.c  -  array: set mean value to zero
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
#include "mathdefs.h"


/* functions */

extern Status ZeromeanCmplx
              (Size size,
               const void *src,
               void *dst)

{

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  const Cmplx *s = src;
  Cmplx *d = dst;
  Size i = 8;

  Real sum2;
  Real sum0 = 0;
  Real squo = 0;
  do {
    Real sumre = 0;
    Real sumim = 0;
    for ( Size j = 0; j < size; j++ ) {
      sumre += Re( s[j] );
      sumim += Im( s[j] );
    }
    Real meanre = sumre / size;
    Real meanim = sumim / size;
    for ( Size j = 0; j < size; j++ ) {
      Cset( d[j], Re( s[j] ) - meanre, Im( s[j] ) - meanim );
    }
    sum2 = sumre * sumre + sumim * sumim;
    if ( sum0 > 0 ) squo = sum2 / sum0;
    sum0 = sum2;
    s = d;
  } while ( ( i-- > 0 ) && ( sum2 > 0 ) && ( squo < 0.01 ) );

  return E_NONE;

}
