/*----------------------------------------------------------------------------*
*
*  suprimio.h  -  imageio: suprim files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef suprimio_h_
#define suprimio_h_

#include "suprimiodefs.h"
#include "imageio.h"

#define SuprimioName   "suprimio"
#define SuprimioVers   ImageioVers
#define SuprimioCopy   ImageioCopy


/* exception codes */

enum {
  E_SUPRIMIO = SuprimioModuleCode,
  E_SUPRIMIO_HDR,
  E_SUPRIMIO_TRC,
  E_SUPRIMIO_MAXCODE
};


/* types */

typedef struct {
  SuprimHeader header;
  Size headersize;
  char *mod;
  Size nmod;
  Size len[3];
  Index low[3];
} SuprimMeta;


/* macros */

#define SuprimOpenFlag 0xffff


/* prototypes */

extern Status SuprimFmt
              (Imageio *imageio);

extern Status SuprimNew
              (Imageio *imageio);

extern Status SuprimOld
              (Imageio *imageio);

extern Status SuprimSiz
              (Imageio *imageio,
               Offset size,
               Size length);

extern Status SuprimGet
              (const Imageio *imageio,
               ImageioMeta *meta);

extern Status SuprimHeaderRead
              (Imageio *imageio,
               SuprimHeader *hdr);

extern Status SuprimHeaderWrite
              (Imageio *imageio);


#endif
