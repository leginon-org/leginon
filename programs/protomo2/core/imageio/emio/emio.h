/*----------------------------------------------------------------------------*
*
*  emio.h  -  imageio: em files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef emio_h_
#define emio_h_

#include "emiodefs.h"
#include "imageio.h"

#define EMioName   "emio"
#define EMioVers   ImageioVers
#define EMioCopy   ImageioCopy


/* exception codes */

enum {
  E_EMIO = EMioModuleCode,
  E_EMIO_HDR,
  E_EMIO_MAXCODE
};


typedef struct {
  EMHeader header;
  Size headersize;
  Size len[3];
  Index low[3];
} EMMeta;


/* prototypes */

extern Status EMFmt
              (Imageio *imageio);

extern Status EMNew
              (Imageio *imageio);

extern Status EMOld
              (Imageio *imageio);

extern Status EMSiz
              (Imageio *imageio,
               Offset size,
               Size length);

extern Status EMGet
              (const Imageio *imageio,
               ImageioMeta *meta);

extern Status EMHeaderRead
              (Imageio *imageio,
               EMHeader *hdr);

extern Status EMHeaderWrite
              (Imageio *imageio);


#endif
