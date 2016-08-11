/*----------------------------------------------------------------------------*
*
*  sample_box.h  -  array: sampling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "samplecommon.h"
#include "baselib.h"
#include "exception.h"


/* functions */

extern Status SampleBox
              (Size dim,
               const Size *srclen,
               const Size *smp,
               const Size *b,
               const Size *dstlen,
               const Size *c,
               Size *srcoffs,
               Size *dstoffs,
               Size *dstbox)

{
  Size d;
  Status status = E_NONE;

  for ( d = 0; d < dim; d++ ) {
    if ( !smp[d] ) return exception( E_ARGVAL );
    if ( ( c != NULL ) && ( c[d] >= dstlen[d] ) ) return exception( E_ARGVAL );
  }

  for ( d = 0; d < dim; d++ ) {
    Size b0 = ( b == NULL ) ? srclen[d] / 2 : b[d];
    Size c0 = ( c == NULL ) ? dstlen[d] / 2 : c[d];
    Size c1;
    if ( MulSize( smp[d], c0, &c1 ) ) return exception( E_INTOVFL );
    if ( c1 > b0 ) {
      srcoffs[d] = 0;
      dstoffs[d] = c0 - b0 / smp[d];
      dstbox[d] = dstlen[d] - dstoffs[d];
      status = E_SAMPLE_CLIP;
    } else {
      srcoffs[d] = b0 - c1;
      dstoffs[d] = 0;
      dstbox[d] = dstlen[d];
    }
    c0 = dstlen[d] - c0;
    if ( b0 < srclen[d] ) {
      b0 = srclen[d] - b0;
      if ( MulSize( smp[d], c0, &c1 ) ) return exception( E_INTOVFL );
      if ( c1 > b0 ) {
        Size c2 = c0 - b0 / smp[d];
        if ( runcheck &&( c2 > dstbox[d] ) ) return exception( E_SAMPLE );
        dstbox[d] -= c2;
        status = E_SAMPLE_CLIP;
      }
    } else {
      if ( runcheck && ( c0 > dstbox[d] ) ) return exception( E_SAMPLE );
      dstbox[d] -= c0;
      if ( smp[d] * dstoffs[d] < srclen[d] ) {
        b0 = b0 - srclen[d];
        dstbox[d] -= b0 / smp[d];
        if ( b0 % smp[d] ) dstbox[d]--;
      } else {
        dstbox[d] = 0;
      }
      status = E_SAMPLE_CLIP;
    }
  }

  return status;

}
