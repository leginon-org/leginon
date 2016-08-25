/*----------------------------------------------------------------------------*
*
*  image.h  -  image: images
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef image_h_
#define image_h_

#include "imagedefs.h"

#define ImageName   "image"
#define ImageVers   IMAGEVERS"."IMAGEBUILD
#define ImageCopy   IMAGECOPY


/* exception codes */

enum {
  E_IMAGE = ImageModuleCode,
  E_IMAGE_DIM,
  E_IMAGE_SIZE,
  E_IMAGE_ZERO,
  E_IMAGE_BOUNDS,
  E_IMAGE_TYPE,
  E_IMAGE_ATTR,
  E_IMAGE_SYM,
  E_IMAGE_WINDOW,
  E_IMAGE_MAXCODE
};


/* types */

typedef enum {
  ImageAsym     = 0x00,
  ImageNodd     = 0x01,
  ImageSymSym   = 0x02,
  ImageSymNeg   = 0x04,
  ImageSymConj  = 0x08,
  ImageRealspc  = 0x00,
  ImageFourspc  = 0x10,
  ImageSymEven  = ImageSymSym,
  ImageSymOdd   = ImageSymSym | ImageSymNeg,
  ImageSymHerm  = ImageSymSym | ImageSymConj,
  ImageSymAHerm = ImageSymSym | ImageSymConj | ImageSymNeg,
  ImageSymMask  = ImageSymSym | ImageSymConj | ImageSymNeg,
  ImageAttrMask = ImageNodd | ImageSymMask | ImageFourspc,
} ImageAttr;

typedef enum {
  ImageModeZero = 0x0100,
  ImageModeCtr  = 0x0200,
  ImageModeSym  = 0x1000,
  ImageModeFou  = 0x2000,
} ImageMode;

typedef struct {
  Size dim;
  Size *len;
  Index *low;
  Type type;
  ImageAttr attr;
} Image;


/* constants */

#define ImageInitializer  (Image){ 0, NULL, NULL, TypeUndef, ImageAsym }


/* prototypes */

extern Status ImageElement
              (const Image *src,
               const Index *ind,
               Size *el);

extern Status ImageElementOffs
              (const Image *src,
               const Index *ind,
               Offset *el);

extern Status ImageWindow
              (const Image *src,
               const Size windim,
               const Size *winlen,
               const Index *winlow,
               Size *dstlen,
               Index *dstlow,
               ImageAttr *dstattr,
               Size *dstori,
               Size *dstsize);

extern Status ImageWindowCyc
              (const Image *src,
               const Size windim,
               const Size *winlen,
               const Index *winlow,
               Size *dstlen,
               Index *dstlow,
               ImageAttr *dstattr,
               Size *dstori,
               Size *dstsize);

extern Status ImageAttrCopy
              (Type srctype,
               ImageAttr srcattr,
               Type *dsttype,
               ImageAttr *dstattr,
               ImageMode mode);

extern Status ImageMetaAlloc
              (Size dim,
               Image *dst);

extern Status ImageMetaRealloc
              (Size dim,
               Image *dst);

extern void ImageMetaFree
            (Image *dst);

extern Status ImageMetaCopy
              (const Image *src,
               Image *dst,
               ImageMode mode);

extern Status ImageMetaCopyAlloc
              (const Image *src,
               Image *dst,
               ImageMode mode);


#endif
