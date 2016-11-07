/*----------------------------------------------------------------------------*
*
*  imagefourier.h  -  fourierop: image transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagefourier_h_
#define imagefourier_h_

#include "fourieropdefs.h"
#include "fourier.h"
#include "image.h"

#define ImageFourierName   "imagefourier"
#define ImageFourierVers   FOURIEROPVERS"."FOURIEROPBUILD
#define ImageFourierCopy   FOURIEROPCOPY


/* exception codes */

enum {
  E_IMAGEFOURIER = ImageFourierModuleCode,
  E_IMAGEFOURIER_MAXCODE
};


/* types */

struct _ImageFourier;

typedef struct _ImageFourier ImageFourier;


typedef struct {
  FourierOpt opt;
  ImageMode mode;
  Size seqdim;
  Size maxdim;
} ImageFourierParam;


/* constants */

#define ImageFourierParamInitializer  (ImageFourierParam){ 0, 0, 0, 0 }


/* prototypes */

extern ImageFourier *ImageFourierInit
                     (const Image *src,
                      Image *dst,
                      const ImageFourierParam *param);

extern Status ImageFourierTransf
              (const ImageFourier *fou,
               const void *src,
               void *dst,
               Size count);

extern Status ImageFourierFinal
              (ImageFourier *fou);

extern Status ImageFourierTransform
              (const Image *src,
               const void *srcaddr,
               Image *dst,
               void *dstaddr,
               Size count,
               const ImageFourierParam *param);


#endif
