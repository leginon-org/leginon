/*----------------------------------------------------------------------------*
*
*  mulint.h  -  core: multiply
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "baselib.h"
#include "exception.h"


/* template */

{
  UTYPE lomsk = 0; lomsk = ~lomsk; lomsk >>= BITS/2;
  UTYPE himsk = ~lomsk;
  UTYPE s1, s2;

  if ( ( src1 == 0 ) || ( src2 == 0 ) ) {
    if ( dst != NULL ) *dst = 0;
    return E_NONE;
  }

  if ( src1 < 0 ) {
    s1 = -( src1 + 1 );
    if ( !++s1 ) return E_INTOVFL;
  } else {
    s1 = src1;
  }

  if ( src2 < 0 ) {
    s2 = -( src2 + 1 );
    if ( !++s2 ) return E_INTOVFL;
  } else {
    s2 = src2;
  }

  UTYPE hi1 = s1 & himsk;
  UTYPE hi2 = s2 & himsk;
  if ( hi1 ) {
    if ( hi2 ) return E_INTOVFL;
    UTYPE lo2 = s2 & lomsk;
    UTYPE d = lo2 * ( hi1 >> BITS/2 );
    if ( d & himsk) return E_INTOVFL;
    d <<= BITS/2;
    UTYPE lo1 = s1 & lomsk;
    UTYPE lo = lo1 * lo2;
    d += lo;
    if ( d < lo ) return E_INTOVFL;
  } else if ( hi2 ) {
    if ( hi1 ) return E_INTOVFL;
    UTYPE lo1 = s1 & lomsk;
    UTYPE d = lo1 * ( hi2 >> BITS/2 );
    if ( d & himsk) return E_INTOVFL;
    d <<= BITS/2;
    UTYPE lo2 = s2 & lomsk;
    UTYPE lo = lo1 * lo2;
    d += lo;
    if ( d < lo ) return E_INTOVFL;
  }

  UTYPE d = s1 * s2;
  if ( ( src1 < 0 ) ^ ( src2 < 0 ) ) {
    if ( ( d - 1 ) >  (UTYPE)-( TYPEMIN + 1 ) ) return E_INTOVFL;
    if ( ( d - 1 ) == (UTYPE)-( TYPEMIN + 1 ) ) {
      if ( dst != NULL ) *dst = TYPEMIN;
    } else {
      if ( dst != NULL ) *dst = -(TYPE)d;
    }
  } else {
    if ( d > (UTYPE)TYPEMAX ) return E_INTOVFL;
    if ( dst != NULL ) *dst = d;
  }

  return E_NONE;

}
