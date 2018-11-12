/*----------------------------------------------------------------------------*
*
*  arrayelement.c  -  array: array operations
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

extern Status ArrayElementOffs
              (Size dim,
               const Size *len,
               Size elsize,
               const Size *ind,
               Offset *el)

{
  Offset off, offs = 0;
  Status status;

  if ( dim-- ) {

    if ( ind[dim] >= len[dim] ) {
      return exception( E_ARRAY_BOUNDS );
    }

    off = offs + ind[dim];
    if ( off < offs) return exception( E_INTOVFL );
    offs = off;

    while ( dim-- ) {

      status = MulOffset( offs, len[dim], &offs );
      if ( status ) return exception( status );

      if ( ind[dim] >= len[dim] ) {
        return exception( E_ARRAY_BOUNDS );
      }

      off = offs + ind[dim];
      if ( off < offs) return exception( E_INTOVFL );
      offs = off;

    }

  }

  if ( el != NULL ) {
    *el = offs;
  }

  return E_NONE;

}
