/*----------------------------------------------------------------------------*
*
*  imagestat.h  -  image: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagestat_h_
#define imagestat_h_

#include "image.h"
#include "statistics.h"

#define ImageStatName   "imagestat"
#define ImageStatVers   IMAGEVERS"."IMAGEBUILD
#define ImageStatCopy   IMAGECOPY


/* exception codes */

enum {
  E_IMAGESTAT = ImageStatModuleCode,
  E_IMAGESTAT_MAXCODE
};


/* types */

typedef enum {
  ImageStatType = 0x01,
  ImageStatSym  = 0x02,
  ImageStatDom  = 0x04,
  ImageStatSize = 0x08,
  ImageStatAll  = 0x0f,
} ImageStatFlags;

typedef struct {
  StatParam stat;
  ImageStatFlags flags;
} ImageStatParam;


/* constants */

#define ImageStatParamInitializer  (ImageStatParam){ StatParamInitializer, 0 }


/* prototypes */

extern Status ImageStat
              (const Image *src,
               const void *srcaddr,
               Stat *dst,
               const ImageStatParam *param);

extern Status ImageStatPrint
              (const char *hdr,
               const Image *src,
               const void *srcaddr,
               const ImageStatParam *param);


#endif
