/*----------------------------------------------------------------------------*
*
*  mulsize.c  -  core: multiply
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


/* functions */

extern Status MulSize
              (Size src1,
               Size src2,
               Size *dst)

{
  Size lomsk = 0; lomsk = ~lomsk; lomsk >>= SizeBits/2;
  Size himsk = ~lomsk;

  if ( ( src1 == 0 ) || ( src2 == 0 ) ) {
    if ( dst != NULL ) {
      *dst = 0;
    }
    return E_NONE;
  }

  Size hi1 = src1 & himsk;
  Size hi2 = src2 & himsk;
  if ( hi1 ) {
    if ( hi2 ) return E_INTOVFL;
    Size lo2 = src2 & lomsk;
    Size d = lo2 * ( hi1 >> (SizeBits/2) );
    if ( d & himsk) return E_INTOVFL;
    d <<= (SizeBits/2);
    Size lo1 = src1 & lomsk;
    Size lo = lo1 * lo2;
    d += lo;
    if ( d < lo ) return E_INTOVFL;
  } else if ( hi2 ) {
    if ( hi1 ) return E_INTOVFL;
    Size lo1 = src1 & lomsk;
    Size d = lo1 * ( hi2 >> (SizeBits/2) );
    if ( d & himsk) return E_INTOVFL;
    d <<= (SizeBits/2);
    Size lo2 = src2 & lomsk;
    Size lo = lo1 * lo2;
    d += lo;
    if ( d < lo ) return E_INTOVFL;
  }

  if ( dst != NULL ) {
    *dst = src1 * src2;
  }

  return E_NONE;

}
