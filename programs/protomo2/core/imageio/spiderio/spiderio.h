/*----------------------------------------------------------------------------*
*
*  spiderio.h  -  imageio: spider files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef spiderio_h_
#define spiderio_h_

#include "spideriodefs.h"
#include "imageio.h"

#define SpiderioName   "spiderio"
#define SpiderioVers   ImageioVers
#define SpiderioCopy   ImageioCopy


/* exception codes */

enum {
  E_SPIDERIO = SpiderioModuleCode,
  E_SPIDERIO_HDR,
  E_SPIDERIO_STACK,
  E_SPIDERIO_MAXCODE
};


typedef struct {
  SpiderHeader header;
  Size headersize;
  Time cre;
  Size len[3];
  Index low[3];
} SpiderMeta;


/* macros */

#define SPIDER_OPENFLAG  0


/* prototypes */

extern Status SpiderFmt
              (Imageio *imageio);

extern Status SpiderNew
              (Imageio *imageio);

extern Status SpiderOld
              (Imageio *imageio);

extern Status SpiderSiz
              (Imageio *imageio,
               Offset size,
               Size length);

extern Status SpiderGet
              (const Imageio *imageio,
               ImageioMeta *meta);

extern Status SpiderHeaderRead
              (Imageio *imageio,
               SpiderHeader *hdr);

extern Status SpiderHeaderWrite
              (Imageio *imageio);


#endif
