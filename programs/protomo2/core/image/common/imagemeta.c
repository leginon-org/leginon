/*----------------------------------------------------------------------------*
*
*  imagemeta.c  -  image: images
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
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status ImageMetaAlloc
              (Size dim,
               Image *dst)

{

  Size *len = malloc( dim * sizeof(Size) );
  if ( len == NULL ) {
    return exception( E_MALLOC );
  }

  Index *low = malloc( dim * sizeof(Index) );
  if ( low == NULL ) { 
    free( len );
    return exception( E_MALLOC );
  }

  dst->dim = dim;
  dst->len = len;
  dst->low = low;

  return E_NONE;

}


extern Status ImageMetaRealloc
              (Size dim,
               Image *dst)

{

  Size *len = realloc( dst->len, dim * sizeof(Size) );
  if ( len == NULL ) {
    return exception( E_MALLOC );
  }

  Index *low = realloc( dst->low, dim * sizeof(Index) );
  if ( low == NULL ) { 
    free( len );
    return exception( E_MALLOC );
  }

  dst->dim = dim;
  dst->len = len;
  dst->low = low;

  return E_NONE;

}


extern void ImageMetaFree
            (Image *dst)

{

  if ( dst != NULL ) {
    if ( dst->len != NULL ) free( dst->len );
    if ( dst->low != NULL ) free( dst->low );
  }

  *dst = ImageInitializer;

}
