/*----------------------------------------------------------------------------*
*
*  imagemaskcommon.c  -  image: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagemaskcommon.h"
#include "exception.h"


/* functions */

static MaskFlags ImageMaskGetFlags
                 (ImageAttr attr,
                  MaskFlags flags)

{

  flags &= ~( MaskModeNodd | MaskModeSym );

  if ( attr & ImageNodd   ) flags |= MaskModeNodd;
  if ( attr & ImageSymSym ) flags |= MaskModeSym;

  if ( ~flags & MaskModeUnit ) {
    if ( attr & ImageFourspc ) {
      flags |= MaskModeFract;
    } else {
      flags &= ~MaskModeFract;
    }
  }

  return flags;

}


extern MaskFlags ImageMaskParam2d
                 (const Size *len,
                  const Index *low,
                  ImageAttr attr,
                  const Coord *c,
                  MaskFlags flags,
                  Coord *b)

{

  flags = ImageMaskGetFlags( attr, flags );

  if ( low == NULL ) {
    if ( flags & MaskModeSym ) {
      b[0] = c[0];
    } else {
      b[0] = c[0] - len[0] / 2;
    }
    b[1] = c[1] - len[1] / 2;
  } else {
    b[0] = c[0] - low[0];
    b[1] = c[1] - low[1];
  }

  return flags;

}


extern MaskFlags ImageMaskParam3d
                 (const Size *len,
                  const Index *low,
                  ImageAttr attr,
                  const Coord *c,
                  MaskFlags flags,
                  Coord *b)

{

  flags = ImageMaskGetFlags( attr, flags );

  if ( low == NULL ) {
    if ( flags & MaskModeSym ) {
      b[0] = c[0];
    } else {
      b[0] = c[0] - len[0] / 2;
    }
    b[1] = c[1] - len[1] / 2;
    b[2] = c[2] - len[2] / 2;
  } else {
    b[0] = c[0] - low[0];
    b[1] = c[1] - low[1];
    b[2] = c[2] - low[2];
  }

  return flags;

}


extern MaskFlags ImageMaskParam
                 (const Image *image,
                  const Coord *c,
                  MaskFlags flags,
                  Coord *b)

{
  Index low;

  flags = ImageMaskGetFlags( image->attr, flags );

  for ( Size d = 0 ; d < image->dim; d++ ) {
    if ( image->low == NULL ) {
      if ( ( d == 0 ) && ( flags & MaskModeSym ) ) {
        low = 0;
      } else {
        low = -(Index)( image->len[d] / 2 );
      }
    } else {
      low = image->low[d];
    }
    b[d] = c[d] - low;
  }

  return flags;

}


extern Status ImageMaskSetParam
              (const Image *image,
               const MaskParam *src,
               MaskParam *dst,
               Coord *b,
               Size bsize)

{

  if ( src->b == NULL ) {

    dst->A = src->A;
    dst->b = NULL;
    dst->wid = src->wid;
    dst->apo = src->apo;
    dst->val = src->val;
    dst->flags = ImageMaskGetFlags( image->attr, src->flags );

  } else {

    if ( image->dim * sizeof(Coord) > bsize ) return exception( E_IMAGEMASK_DIM );

    dst->A = src->A;
    dst->b = b;
    dst->wid = src->wid;
    dst->apo = src->apo;
    dst->val = src->val;
    dst->flags = ImageMaskParam( image, src->b, src->flags, b );

  }

  return E_NONE;

}
