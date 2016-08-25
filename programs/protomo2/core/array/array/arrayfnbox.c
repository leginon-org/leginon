/*----------------------------------------------------------------------------*
*
*  arrayfnbox.c  -  array: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "array.h"
#include "baselib.h"
#include "exception.h"


/* functions */

extern Status ArrayFnBox
              (Size dim,
               const Size *len,
               const Size *ori,
               const Size *box,
               Size elsize,
               Size *dst,
               Offset *size)

{
  Size d, dstlen;
  Offset dstsize = dim ? elsize : 0;
  Status ovfl = E_NONE, status = E_NONE;

  if ( len == NULL ) return exception( E_ARGVAL );
  if ( box == NULL ) return exception( E_ARGVAL );

  for ( d = 0; d < dim; d++ ) {

    if ( ori == NULL ) {

      dstlen = len[d];
      if ( dstlen < box[d] ) {
        if ( !status ) {
          status = exception( E_ARRAY_BOUNDS );
        }
      } else {
        dstlen = box[d];
      }

    } else if ( ori[d] < len[d] ) {

      dstlen = len[d] - ori[d];
      if ( dstlen < box[d] ) {
        if ( !status ) {
          status = exception( E_ARRAY_BOUNDS );
        }
      } else {
        dstlen = box[d];
      }

    } else {

      dstlen = 0;
      if ( !status ) {
        status = exception( E_ARRAY_BOUNDS );
      }

    }

    if ( dst != NULL ) dst[d] = dstlen;

    if ( MulOffset( dstsize, dstlen, &dstsize ) ) {
      if ( !ovfl ) ovfl = exception( E_INTOVFL );
    }

  }

  if ( size == NULL ) {
    if ( ovfl ) {
      status = ovfl;
    } else if ( !status && !dstsize ) {
      status = exception( E_ARRAY_ZERO );
    }
  } else if ( ovfl ) {
    status = ovfl;
    *size = 0;
  } else {
    *size = elsize ? ( dstsize / elsize ) : 0;
  }

  return status;

}
