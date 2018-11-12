/*----------------------------------------------------------------------------*
*
*  tiffiodefs.h  -  imageio: TIFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tiffiodefs_h_
#define tiffiodefs_h_

#include "defs.h"


/* types */

typedef enum {
  TIFFIO_SMP_INT  = 0x0001,
  TIFFIO_SMP_UINT = 0x0002,
  TIFFIO_SMP_SGN  = 0x0004,
  TIFFIO_ORI_RIG  = 0x0010,
  TIFFIO_ORI_TOP  = 0x0020,
  TIFFIO_TRNSP    = 0x0040,
} TiffioFlags;

typedef struct {
  TiffioFlags flags;
  float DPI;
  uint16_t compression;
} TiffioOptions;


#endif
