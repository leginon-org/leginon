/*----------------------------------------------------------------------------*
*
*  imagearray.h  -  image: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagearray_h_
#define imagearray_h_

#include "image.h"
#include "array.h"

#define ImageArrayName   "imagearray"
#define ImageArrayVers   IMAGEVERS"."IMAGEBUILD
#define ImageArrayCopy   IMAGECOPY


/* exception codes */

enum {
  E_IMAGEARRAY = ImageArrayModuleCode,
  E_IMAGEARRAY_SYMSIZE,
  E_IMAGEARRAY_ASYM,
  E_IMAGEARRAY_MAXCODE
};


/* types */

typedef Status (*ImageFn)(Type, Size, const void *, const void *, Size, void *);

typedef struct {
  ImageFn asym;
  ImageFn even;
  ImageFn odd;
  ImageFn herm;
  ImageFn aherm;
} ImageFnTab;


/* prototypes */

extern Status ImageFnExec
              (const ImageFnTab *fn,
               const Image *src,
               const void *srcaddr,
               void *dstaddr,
               ImageMode mode);

extern Status ImageFnsExec
              (const ImageFnTab *fn,
               const Image *src,
               const void *srcaddr,
               void *dstaddr);

extern Status ImageExtend
              (const Image *src,
               const void *srcaddr,
               const Image *dst,
               void *dstaddr,
               ImageMode mode);

extern Status ImageSumAbs2
              (const Image *src,
               const void *srcaddr,
               void *dstaddr);


#endif
