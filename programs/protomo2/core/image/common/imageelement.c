/*----------------------------------------------------------------------------*
*
*  imageelement.c  -  image: images
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "image.h"
#include "array.h"
#include "baselib.h"
#include "exception.h"


/* functions */

extern Status ImageElement
              (const Image *src,
               const Index *ind,
               Size *el)

{
  Size offs = 0;
  Index low;
  Size off;
  Status status;

  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( ind == NULL ) ) return exception( E_ARGVAL );

  Size dim = src->dim;
  if ( dim ) {
    if ( src->len == NULL ) return exception( E_IMAGE );
  }

  if ( dim-- ) {

    if ( src->attr & ImageSymSym ) {
      if ( dim ) {
        low = ( src->low == NULL ) ? ( -(Index)( src->len[dim] / 2 ) ) : src->low[dim];
      } else {
        low = 0;
      }
    } else {
      low = ( src->low == NULL ) ? 0 : src->low[dim];
    }
    if ( ind[dim] < low ) {
      return exception( E_ARRAY_BOUNDS );
    }

    off = ind[dim] - low;
    if ( off >= src->len[dim] ) {
      return exception( E_ARRAY_BOUNDS );
    }
    offs += off;
    if ( offs < off ) {
      return exception( E_INTOVFL );
    }

    while ( dim-- ) {

      status = MulSize( offs, src->len[dim], &offs );
      if ( status ) return exception( status );

      if ( src->attr & ImageSymSym ) {
        if ( dim ) {
          low = ( src->low == NULL ) ? ( -(Index)( src->len[dim] / 2 ) ) : src->low[dim];
        } else {
          low = 0;
        }
      } else {
        low = ( src->low == NULL ) ? 0 : src->low[dim];
      }
      if ( ind[dim] < low ) {
        return exception( E_ARRAY_BOUNDS );
      }

      off = ind[dim] - low;
      if ( off >= src->len[dim] ) {
        return exception( E_ARRAY_BOUNDS );
      }
      offs += off;
      if ( offs < off ) {
        return exception( E_INTOVFL );
      }

    }

  }

  if ( el != NULL ) {
    *el = offs;
  }

  return E_NONE;

}
