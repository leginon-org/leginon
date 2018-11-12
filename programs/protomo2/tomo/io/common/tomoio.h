/*----------------------------------------------------------------------------*
*
*  tomoio.h  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoio_h_
#define tomoio_h_

#include "tomoiodefs.h"
#include "tomometa.h"
#include "imageio.h"
#include "i3data.h"

#define TomoioName   "tomoio"
#define TomoioVers   TOMOIOVERS"."TOMOIOBUILD
#define TomoioCopy   TOMOIOCOPY


/* exception codes */

enum {
  E_TOMOIO = TomoioModuleCode,
  E_TOMOIO_OP,
  E_TOMOIO_DIM,
  E_TOMOIO_META,
  E_TOMOIO_REQ,
  E_TOMOIO_MAXCODE
};


/* types */

struct _Tomoio;

typedef struct _Tomoio Tomoio;


/* prototypes */

extern Tomoio *TomoioCreate
               (const char *path,
                const char *prfx,
                const Size count,
                const Image *image,
                const char *fmt);

extern Tomoio *TomoioOpenReadOnly
               (const char *path,
                const char *prfx,
                Size *count,
                I3Image *image);

extern Tomoio *TomoioSetAlloc
               (const Size count,
                const Image *image);

extern Status TomoioClose
              (Tomoio *tomoio,
               Status fail);

extern Status TomoioSetOffset
              (Tomoio *tomoio,
               Offset offset);

extern Status TomoioGetOffset
              (Tomoio *tomoio);

extern Status TomoioSetSize
              (Tomoio *tomoio);

extern Status TomoioGetCount
              (Tomoio *tomoio,
               Size *count);

extern const I3data *TomoioGetExtra
                     (const Tomoio *tomoio);

extern Status TomoioAddr
              (const Tomoio *tomoio,
               Offset offset,
               Size length,
               void **addr);

extern Status TomoioRead
              (const Tomoio *tomoio,
               Offset offset,
               Size length,
               void *buf);

extern Status TomoioReadBuf
              (const Tomoio *tomoio,
               Offset offset,
               Size length,
               void **buf);

extern Status TomoioWrite
              (const Tomoio *tomoio,
               Offset offset,
               Size length,
               const void *buf);

extern void TomoioPrintImage
            (const Tomoio *tomoio);

extern Status TomoioExtraSetSampling
              (Tomoio *tomoio,
               Coord sampling);


#endif
