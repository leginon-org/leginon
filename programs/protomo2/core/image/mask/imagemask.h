/*----------------------------------------------------------------------------*
*
*  imagemask.h  -  image: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagemask_h_
#define imagemask_h_

#include "image.h"
#include "mask.h"

#define ImageMaskName   "imagemask"
#define ImageMaskVers   IMAGEVERS"."IMAGEBUILD
#define ImageMaskCopy   IMAGECOPY


/* exception codes */

enum {
  E_IMAGEMASK = ImageMaskModuleCode,
  E_IMAGEMASK_DIM,
  E_IMAGEMASK_FUNC,
  E_IMAGEMASK_MAXCODE
};


/* prototypes */

extern Status ImageMask
              (const Image *image,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status ImageMaskRect
              (const Image *image,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status ImageMaskEllips
              (const Image *image,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status ImageMaskGauss
              (const Image *image,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status ImageMaskWedge
              (const Image *image,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern MaskFlags ImageMaskParam
                 (const Image *image,
                  const Coord *c,
                  MaskFlags flags,
                  Coord *b);

extern MaskFlags ImageMaskParam2d
                 (const Size *len,
                  const Index *low,
                  ImageAttr attr,
                  const Coord *c,
                  MaskFlags flags,
                  Coord *b);

extern MaskFlags ImageMaskParam3d
                 (const Size *len,
                  const Index *low,
                  ImageAttr attr,
                  const Coord *c,
                  MaskFlags flags,
                  Coord *b);


#endif
