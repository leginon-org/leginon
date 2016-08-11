/*----------------------------------------------------------------------------*
*
*  tiffiocommon.h  -  imageio: TIFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tiffiocommon_h_
#define tiffiocommon_h_

#include "tiffiodefs.h"
#include "imageio.h"
#include <stdarg.h>
#include <tiffio.h>

#define TiffioName   "tiffio"
#define TiffioVers   ImageioVers
#define TiffioCopy   ImageioCopy


/* exception codes */

enum {
  E_TIFFIO = TiffioModuleCode,
  E_TIFFIO_ERR,
  E_TIFFIO_IMPL,
  E_TIFFIO_MAXCODE
};


/* types */

typedef struct {
  uint16_t sampfmt;
  uint16_t sampsiz[3];
  uint16_t sampnum;
  uint32_t rowsperstrip;
  uint32_t tilewidth;
  uint32_t tilelength;
  float  xresolution; /* TIFF 6.0 Specification defines data type as RATIONAL not float */
  float  yresolution; /* TIFF 6.0 Specification defines data type as RATIONAL not float */
  uint16_t resolutionunit;
  uint16_t compression;
  uint16_t photometric;
  uint16_t fillorder;
  uint16_t orientation;
  uint16_t planarconfig;
} TiffioMetaTags;

typedef struct {
  TIFF *handle;
  TiffioMetaTags tags;
  uint32_t flags;
  Time cre;
  Time mod;
  Size len[2];
  Index low[2];
} TiffioMeta;


/* macros */

#define TIFFIO_DATE      0x008000
#define TIFFIO_TILED     0x010000
#define TIFFIO_INIT      0x100000
#define TIFFIO_RD        0x200000
#define TIFFIO_WR        0x400000
#define TIFFIO_MOD       0x800000


/* variables */

extern TiffioOptions TiffioOpt;


/* prototypes */

extern Status TiffioFmt
              (Imageio *imageio);

extern Status TiffioNew
              (Imageio *imageio);

extern Status TiffioOld
              (Imageio *imageio);

extern Status TiffioSyn
              (Imageio *imageio);

extern Status TiffioFls
              (Imageio *imageio);

extern Status TiffioFin
              (Imageio *imageio);

extern Status TiffioGet
              (const Imageio *imageio,
               ImageioMeta *meta);

extern Status TiffioRd
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr);

extern Status TiffioWr
              (Imageio *imageio,
               Offset offset,
               Size length,
               const void *addr);

extern void TiffioError
            (const char* module,
             const char* fmt,
             va_list ap);

extern Status TiffioOpen
              (Imageio *imageio);

extern void TiffSignConvert
              (Type type,
               void *buf,
               Size len);

extern Status TiffioLoadTiles
              (Imageio *imageio,
               void *buf);


#endif
