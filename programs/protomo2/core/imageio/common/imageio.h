/*----------------------------------------------------------------------------*
*
*  imageio.h  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imageio_h_
#define imageio_h_

#include "imageiodefs.h"
#include "image.h"

#define ImageioName   "imageio"
#define ImageioVers   IMAGEIOVERS"."IMAGEIOBUILD
#define ImageioCopy   IMAGEIOCOPY


/* exception codes */

enum {
  E_IMAGEIO = ImageioModuleCode,
  E_IMAGEIO_FIN,
  E_IMAGEIO_FMT,
  E_IMAGEIO_CAP,
  E_IMAGEIO_IOP,
  E_IMAGEIO_DIM,
  E_IMAGEIO_BIG,
  E_IMAGEIO_SWP,
  E_IMAGEIO_TYPE,
  E_IMAGEIO_ATTR,
  E_IMAGEIO_DOMAIN,
  E_IMAGEIO_VERS,
  E_IMAGEIO_OFFS,
  E_IMAGEIO_FORMAT,
  E_IMAGEIO_FMTERR,
  E_IMAGEIO_DATA,
  E_IMAGEIO_RD,
  E_IMAGEIO_WR,
  E_IMAGEIO_SZ,
  E_IMAGEIO_MAXCODE
};


/* types */

struct _Imageio;

typedef struct _Imageio Imageio;

typedef enum {
  ImageioCapLib  = 0x01,
  ImageioCapUnix = 0x02,
  ImageioCapStd  = 0x04,
  ImageioCapMmap = 0x08,
  ImageioCapAmap = 0x10,
  ImageioCapLoad = 0x20,
  ImageioCapRdWr = 0x03,
  ImageioCapAll  = 0x3f,
  ImageioCapAuto = 0x80,
} ImageioCap;

typedef enum {
  ImageioModeCre  = 0x01,
  ImageioModeDel  = 0x02,
  ImageioModeRd   = 0x10,
  ImageioModeWr   = 0x20,
  ImageioModeLd   = 0x40,
  ImageioModeMask = 0xff,
} ImageioMode;

typedef struct {
  char format[16];
  char version[16];
  char endian;
  Time cre;
  Time mod;
  ImageioCap cap;
  ImageioMode mode;
} ImageioMeta;

typedef struct {
  const char *filepath;
  const char *format;
  ImageioMode mode;
  ImageioCap cap;
} ImageioParam;


/* constants */

#define ImageioParamInitializer  (ImageioParam){ NULL, NULL, 0, ImageioCapRdWr | ImageioCapStd | ImageioCapMmap | ImageioCapLoad | ImageioCapAuto }


/* variables */

extern ImageioParam ImageioParamDefault;


/* prototypes */

extern Imageio *ImageioCreate
               (const char *path,
                const Image *image,
                const ImageioParam *param);

extern Imageio *ImageioOpenReadOnly
               (const char *path,
                Image *image,
                const ImageioParam *param);

extern Imageio *ImageioOpenReadWrite
               (const char *path,
                Image *image,
                const ImageioParam *param);

extern Status ImageioClose
              (Imageio *imageio);

extern Status ImageioDel
              (Imageio *imageio);

extern Status ImageioUndel
              (Imageio *imageio);

extern Status ImageioStd
              (Imageio *imageio);

extern Status ImageioMmap
              (Imageio *imageio);

extern Status ImageioAmap
              (Imageio *imageio);

extern Status ImageioResize
              (Imageio *imageio,
               Size length);

extern Status ImageioRead
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr);

extern Status ImageioWrite
              (Imageio *imageio,
               Offset offset,
               Size length,
               const void *addr);

extern Status ImageioAddr
              (Imageio *imageio,
               Offset offset,
               Size length,
               void **addr);

extern void *ImageioBeginRead
             (Imageio *imageio,
              Offset offset,
              Size length);

extern void *ImageioBeginWrite
             (Imageio *imageio,
              Offset offset,
              Size length);

extern Status ImageioEndRead
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr);

extern Status ImageioEndWrite
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr);

extern void *ImageioIn
             (const char *path,
              Image *image,
              const ImageioParam *param);

extern Status ImageioOut
              (const char *path,
               const Image *image,
               const void *addr,
               const ImageioParam *param);

extern const char *ImageioGetPath
                   (const Imageio *imageio);

extern const char *ImageioGetFormat
                   (const Imageio *imageio);

extern IOMode ImageioGetMode
              (const Imageio *imageio);

extern Status ImageioGetMeta
              (const Imageio *imageio,
               ImageioMeta *meta);

extern Size ImageioGetDim
            (const Imageio *imageio);

extern const Size *ImageioGetLen
                   (const Imageio *imageio);

extern const Index *ImageioGetLow
                    (const Imageio *imageio);

extern Type ImageioGetType
            (const Imageio *imageio);

extern ImageAttr ImageioGetAttr
                 (const Imageio *imageio);

extern void *ImageioGetFormatOpt
             (const char *format);

extern Status ImageioFormatCheck
              (const char *format);

extern ImageioCap ImageioCapCheck
                  (const char *cap);

extern Status ImageioErrPath
              (Imageio *imageio,
               Status status);


#endif
