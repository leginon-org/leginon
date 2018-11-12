/*----------------------------------------------------------------------------*
*
*  imageiomodule.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageio.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ImageioExceptions[ E_IMAGEIO_MAXCODE - E_IMAGEIO ] = {
  { "E_IMAGEIO",        "internal error ("ImageioName")" },
  { "E_IMAGEIO_FIN",    "finalization error" },
  { "E_IMAGEIO_FMT",    "unknown image file format" },
  { "E_IMAGEIO_CAP",    "unsupported i/o capability" },
  { "E_IMAGEIO_IOP",    "unsupported i/o operation" },
  { "E_IMAGEIO_DIM",    "unsupported image dimension" },
  { "E_IMAGEIO_BIG",    "image too big" },
  { "E_IMAGEIO_SWP",    "wrong byte order for memory mapping" },
  { "E_IMAGEIO_TYPE",   "unsupported image data type" },
  { "E_IMAGEIO_ATTR",   "unsupported image storage mode" },
  { "E_IMAGEIO_DOMAIN", "unsupported image domain" },
  { "E_IMAGEIO_VERS",   "unsupported image file format version" },
  { "E_IMAGEIO_OFFS",   "invalid i/o operation (offset/size)" },
  { "E_IMAGEIO_FORMAT", "wrong image file format" },
  { "E_IMAGEIO_FMTERR", "image format validation failure" },
  { "E_IMAGEIO_DATA",   "image was not closed properly, may be corrupt" },
  { "E_IMAGEIO_RD",     "no read permission" },
  { "E_IMAGEIO_WR",     "no write permission" },
  { "E_IMAGEIO_SZ",     "invalid resize request" },
};


/* module initialization/finalization */

#ifdef ENABLE_DYNAMIC

static const ModuleTable ImageioTable[] = {
  { "lib"LIBPRFX"ccp4io.so",   "CCP4ioModule",   "ccp4io"   },
  { "lib"LIBPRFX"emio.so",     "EMioModule",     "emio"     },
  { "lib"LIBPRFX"imagicio.so", "ImagicioModule", "imagicio" },
  { "lib"LIBPRFX"spiderio.so", "SpiderioModule", "spiderio" },
  { "lib"LIBPRFX"suprimio.so", "SuprimioModule", "suprimio" },
  { "lib"LIBPRFX"tiffio.so",   "TiffioModule",   "tiffio"   },
  {  NULL,                      NULL,             NULL      }
};

#endif /* ENABLE_DYNAMIC */


static Status ImageioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ImageioExceptions, E_IMAGEIO, E_IMAGEIO_MAXCODE );
  if ( exception( status ) ) return status;

#ifdef ENABLE_DYNAMIC
  status = ModuleDynRegisterTable( ImageioTable, ImageioVers );
  if ( exception( status ) ) return status;
#endif /* ENABLE_DYNAMIC */

  return E_NONE;

}


/* module descriptor */

const Module ImageioModule = {
  ImageioName,
  ImageioVers,
  ImageioCopy,
  COMPILE_DATE,
  ImageioModuleInit,
  NULL,
  NULL,
};
