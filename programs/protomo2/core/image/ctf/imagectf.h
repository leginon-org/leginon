/*----------------------------------------------------------------------------*
*
*  imagectf.h  -  image: contrast transfer function
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagectf_h_
#define imagectf_h_

#include "image.h"
#include "emdefs.h"

#define ImageCTFName   "imagectf"
#define ImageCTFVers   IMAGEVERS"."IMAGEBUILD
#define ImageCTFCopy   IMAGECOPY


/* exception codes */

enum {
  E_IMAGECTF = ImageCTFModuleCode,
  E_IMAGECTF_DIM,
  E_IMAGECTF_TYPE,
  E_IMAGECTF_MAXCODE
};


/* types */

typedef struct {
  Coord pixel;   /* nm */
  Coord dz;      /* nm */
  Coord ca;
  Coord phia;    /* degrees */
  Coord ampcon;  /* degrees */
} ImageCTFParam;


/* constants */

#define ImageCTFParamInitializer (ImageCTFParam){ 0, 0, 0, 0, 0 }


/* prototypes */

extern Status ImageCTF
              (const Image *image,
               void *addr,
               const EMparam *empar,
               const ImageCTFParam *param);

extern Status ImageCTFReal
              (const Image *image,
               void *addr,
               const EMparam *empar,
               const ImageCTFParam *param);

extern Status ImageCTFCmplx
              (const Image *image,
               void *addr,
               const EMparam *empar,
               const ImageCTFParam *param);

extern Status ImageCTFPrintParam
              (const EMparam *empar,
               const ImageCTFParam *param);


#endif
