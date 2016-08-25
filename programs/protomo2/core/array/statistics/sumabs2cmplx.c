/*----------------------------------------------------------------------------*
*
*  sumabs2cmplx.c  -  array: calculate sum of squared absolute value
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

extern Status Sumabs2Cmplx
              (Size size,
               const void *src,
               void *dst)

{

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( dst == NULL ) return exception( E_ARGVAL );

  const Cmplx *s = src;
  Real *d = dst;

  Real re2 = 0;
  Real im2 = 0;
  s += size;
  while ( s-- != src ) {
    Real re = Re( *s );
    Real im = Im( *s );
    re2 += re * re;
    im2 += im * im;
  }
  *d = re2 + im2;

  return E_NONE;

}
