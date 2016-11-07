/*----------------------------------------------------------------------------*
*
*  imagecopy.c  -  image: images
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

extern Status ImageMetaCopy
              (const Image *src,
               Image *dst,
               ImageMode mode)

{
  Status status;

  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst == NULL ) ) return exception( E_ARGVAL );

  if ( src->dim ) {
    if ( ( src != NULL ) && ( src->len == NULL ) ) return exception( E_IMAGE );
    if ( ( dst != NULL ) && ( dst->len == NULL ) ) return exception( E_IMAGE );
  }

  if ( ( mode & ( ImageModeZero | ImageModeCtr ) ) == ( ImageModeZero | ImageModeCtr ) ) {
    return exception( E_ARGVAL );
  }

  status = ImageAttrCopy( src->type, src->attr, &dst->type, &dst->attr, mode );
  if ( exception( status ) ) return status;
  dst->attr &= ~ImageNodd;

  dst->dim = src->dim;
  if ( dst->dim == 0 ) return E_NONE;

  if ( src->attr & ImageSymSym ) {

    if ( ( src->low != NULL ) && ( src->low[0] != 0 ) ) {
      return exception( E_IMAGE_SYM );
    }

    if ( dst->attr & ImageSymSym ) {

      /* sym to sym */
      dst->attr |= src->attr & ImageNodd;
      for ( Size d = 0; d < src->dim; d++ ) {
        dst->len[d] = src->len[d];
      }
      if ( dst->low != NULL ) {
        dst->low[0] = 0;
        for ( Size d = 1; d < src->dim; d++ ) {
          if ( mode & ImageModeZero ) {
            dst->low[d] = 0;
          } else {
            dst->low[d] = -(Index)( src->len[d] / 2 );
          }
        }
      }

    } else {

      /* sym to asym */
      if ( src->len[0] ) {
        dst->len[0] = 2 * ( src->len[0] - 1 );
        if ( src->attr & ImageNodd ) dst->len[0]++;
      } else {
        dst->len[0] = 0;
      }
      for ( Size d = 1; d < src->dim; d++ ) {
        dst->len[d] = src->len[d];
      }
      if ( dst->low != NULL ) {
        for ( Size d = 0; d < src->dim; d++ ) {
          if ( mode & ImageModeZero ) {
            dst->low[d] = 0;
          } else if ( ( mode & ImageModeCtr ) || ( dst->attr & ImageFourspc ) ) {
            dst->low[d] = -(Index)( dst->len[d] / 2 );
          } else {
            dst->low[d] = 0;
          }
        }
      }

    }

  } else {

    if ( dst->attr & ImageSymSym ) {

      /* asym to sym */
      if ( src->len[0] % 2 ) {
        dst->attr |= ImageNodd;
      }
      if ( src->len[0] ) {
        dst->len[0] = src->len[0] / 2 + 1;
      } else {
        dst->len[0] = 0;
      }
      for ( Size d = 1; d < src->dim; d++ ) {
        dst->len[d] = src->len[d];
      }
      if ( dst->low != NULL ) {
        dst->low[0] = 0;
        for ( Size d = 1; d < src->dim; d++ ) {
          if ( mode & ImageModeZero ) {
            dst->low[d] = 0;
          } else {
            dst->low[d] = -(Index)( src->len[d] / 2 );
          }
        }
      }

    } else {

      /* asym to asym */
      for ( Size d = 0; d < src->dim; d++ ) {
        dst->len[d] = src->len[d];
      }
      if ( dst->low != NULL ) {
        for ( Size d = 0; d < src->dim; d++ ) {
          if ( mode & ImageModeZero ) {
            dst->low[d] = 0;
          } else if ( ( mode & ImageModeCtr ) || ( dst->attr & ImageFourspc ) ) {
            dst->low[d] = -(Index)( src->len[d] / 2 );
          } else if ( ( src->low == NULL ) || ( src->attr & ImageFourspc ) ) {
            dst->low[d] = 0;
          } else {
            dst->low[d] = src->low[d];
          }
        }
      }

    }

  }

  return E_NONE;

}


extern Status ImageMetaCopyAlloc
              (const Image *src,
               Image *dst,
               ImageMode mode)

{
  Status status;

  status = ImageMetaAlloc( src->dim, dst );
  if ( exception( status ) ) return status;

  status = ImageMetaCopy( src, dst, mode );
  if ( exception( status ) ) {
    free( dst->len ); dst->len = NULL;
    free( dst->low ); dst->low = NULL;
    return status;
  }

  return E_NONE;

}
