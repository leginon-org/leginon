/*----------------------------------------------------------------------------*
*
*  ccp4io.h  -  imageio: CCP4 files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef ccp4io_h_
#define ccp4io_h_

#include "ccp4iodefs.h"
#include "imageio.h"

#define CCP4ioName   "ccp4io"
#define CCP4ioVers   ImageioVers
#define CCP4ioCopy   ImageioCopy


/* exception codes */

enum {
  E_CCP4IO = CCP4ioModuleCode,
  E_CCP4IO_FOU,
  E_CCP4IO_AXIS,
  E_CCP4IO_MAXCODE
};


/* types */

typedef struct {
  CCP4Header header;
  uint32_t mode;
  uint32_t ilab;
  Size len[3];
  Index low[3];
} CCP4Meta;


/* macros */

#define CCP4_UNDEF    0xfffe
#define CCP4_OPENFLAG 0xffff


/* prototypes */

extern Status CCP4Fmt
              (Imageio *imageio);

extern Status CCP4New
              (Imageio *imageio);

extern Status CCP4Old
              (Imageio *imageio);

extern Status CCP4Siz
              (Imageio *imageio,
               Offset size,
               Size length);

extern Status CCP4Extra
              (Imageio *imageio,
               IOMode mode,
               void *extra);

extern Status CCP4Get
              (const Imageio *imageio,
               ImageioMeta *meta);

extern Status CCP4HeaderRead
              (Imageio *imageio,
               CCP4Header *hdr);

extern Status CCP4HeaderWrite
              (Imageio *imageio);


#endif
