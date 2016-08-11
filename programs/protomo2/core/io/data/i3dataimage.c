/*----------------------------------------------------------------------------*
*
*  i3data.c  -  io: i3 data
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3data.h"
#include "array.h"
#include "exception.h"
#include "macros.h"


/* functions */

extern Status I3dataGetImage
              (const Image *image,
               I3Image *i3image)

{
  Status status;

  if ( argcheck( image == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( i3image == NULL ) ) return exception( E_ARGVAL );

  if ( image->dim > 4 ) return exception( E_ARRAY_DIM );
  if ( image->len == NULL ) return exception( E_I3DATA );

  Size dim = MIN( image->dim, 3 );
  while ( ( dim > 1 ) && ( image->len[dim-1] == 1 ) ) dim--;

  Size size, elsize = TypeGetSize( image->type );
  status = ArraySize( dim, image->len, elsize, &size );
  if ( exception( status ) ) return status;
  if ( !size ) return exception( E_ARRAY_ZERO );
  if ( size > (Size)OffsetMaxSize ) return exception( E_INTOVFL );

  if ( ( &i3image->image != image ) || ( i3image->len != image->len ) ) {

    for ( Size d = 0; d < dim; d++ ) {
      i3image->len[d] = image->len[d];
      if ( image->low == NULL ) {
        i3image->low[d] = -(Index)( i3image->len[d] / 2 );
      } else {
        i3image->low[d] = image->low[d];
      }
    }

  }

  for ( Size d = dim; d < 3; d++ ) {
    i3image->len[d] = 1;
    i3image->low[d] = 0;
  }

  i3image->len[3] = ( image->dim < 4 ) ? 0 : image->len[3];
  i3image->low[3] = 0;

  i3image->image.dim = dim;
  i3image->image.len = i3image->len;
  i3image->image.low = i3image->low;
  i3image->image.type = image->type;
  i3image->image.attr = image->attr;

  i3image->size = size;
  i3image->elsize = elsize;

  return E_NONE;

}
