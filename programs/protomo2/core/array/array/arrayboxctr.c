/*----------------------------------------------------------------------------*
*
*  arrayboxctr.c  -  array: array operations
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

extern Status ArrayBoxCtr
              (Size dim,
               const Size *len,
               const Size *ctr,
               const Size *box,
               Size *ori,
               Size *pos,
               Size *dst,
               Size *size)

{
  Size d, dstlen;
  Size dstsize = dim ? 1 : 0;
  Size srcori, dstpos, boxlen;
  Status ovfl = E_NONE, status = E_NONE;

  if ( len == NULL ) return exception( E_ARGVAL );
  if ( box == NULL ) return exception( E_ARGVAL );

  for ( d = 0; d < dim; d++ ) {

    Size srcctr = ( ctr == NULL ) ? len[d] / 2 : ctr[d];

    if ( srcctr < box[d] / 2 ) {
      srcori = 0;
      dstpos = box[d] / 2 - srcctr;
      boxlen = ( dstpos < box[d] ) ? box[d] - dstpos : 0;
      if ( !status ) {
        status = exception( E_ARRAY_BOUNDS );
      }
    } else {
      srcori = srcctr - box[d] / 2;
      dstpos = 0;
      boxlen = box[d];
    }

    if ( srcori < len[d] ) {

      dstlen = len[d] - srcori;
      if ( dstlen < boxlen ) {
        if ( !status ) {
          status = exception( E_ARRAY_BOUNDS );
        }
      } else {
        dstlen = boxlen;
      }

    } else {

      dstlen = 0;
      if ( !status ) {
        status = exception( E_ARRAY_BOUNDS );
      }

    }

    if ( ori != NULL ) ori[d] = srcori;

    if ( pos != NULL ) pos[d] = dstpos;

    if ( dst != NULL ) dst[d] = dstlen;

    if ( MulSize( dstsize, dstlen, &dstsize ) ) {
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
    *size = dstsize;
  }

  return status;

}
