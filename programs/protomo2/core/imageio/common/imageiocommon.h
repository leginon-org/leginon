/*----------------------------------------------------------------------------*
*
*  imageiocommon.h  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imageiocommon_h_
#define imageiocommon_h_

#include "imageio.h"
#include "fileio.h"


/* types */

typedef struct {
  const char *ident;
  uint16_t major;
  uint16_t minor;
} ImageioFormatVersion;

typedef struct {
  ImageioFormatVersion version;
  Status (*fmt)( Imageio * );
  Status (*new)( Imageio * );
  Status (*old)( Imageio * );
  Status (*fls)( Imageio * );
  Status (*syn)( Imageio * );
  Status (*fin)( Imageio * );
  Status (*siz)( Imageio *, Offset, Size );
  Status (*adr)( Imageio *, Offset, Size, void ** );
  Status (*ext)( Imageio *, IOMode, void *);
  Status (*get)( const Imageio *, ImageioMeta * );
  void *opt;
  ImageioCap cap;
  uint16_t prio;
} ImageioFormat;

typedef enum {
  ImageioBigNative = 0x0000100, /* byte order, set if big endian, clear if little endian */
  ImageioBigFile   = 0x0000200,
  ImageioByteSwap  = 0x0000400, /* set if byte order requires conversion */
  ImageioBlkFlipX  = 0x0001000, /* indicate flip image in x-direction */
  ImageioBlkFlipY  = 0x0002000, /* indicate flip image in y-direction */
  ImageioBlkTrnsp  = 0x0004000, /* indicate transpose image */
  ImageioBlk       = 0x0008000, /* use 2D block i/o */
  ImageioFmtAuto   = 0x0010000, /* indicate format autodetection */
  ImageioModeFmt   = 0x0020000, /* indicate format detected successfully */
  ImageioModeOpen  = 0x0040000, /* indicate file opened successfully */
  ImageioModeErr   = 0x0080000, /* indicate error */
  ImageioModData   = 0x0100000, /* indicate data modified */
  ImageioModMeta   = 0x0200000, /* indicate meta data modified */
  ImageioFinMod    = 0x0400000, /* indicate file modified */
  ImageioFinClose  = 0x0800000, /* indicate close operation */
  ImageioAllocLow  = 0x1000000, /* malloc'ed low field */
  ImageioAllocLen  = 0x2000000, /* malloc'ed len field */
  ImageioAllocMeta = 0x4000000, /* malloc'ed meta field */
  ImageioAllocBuf  = 0x8000000, /* malloc'ed temp buffer */
} ImageioStatus;

struct _Imageio {
  Fileio *fileio;
  const ImageioFormat *format;
  ImageioCap cap;
  Size dim;
  Size *len;
  Index *low;
  Type eltype;
  ImageAttr attr;
  Offset arrsize;
  Offset offset;
  void *amap;
  Size amapsize;
  void *meta;
  Size cvtcount;
  void (*rdcvt)( Size, const void *, void * );
  void (*wrcvt)( Size, const void *, void * );
  Status (*rd)( Imageio *, Offset, Size, void * );
  Status (*wr)( Imageio *, Offset, Size, const void * );
  Status (*wra)( Imageio *, Offset, Size, const void * );
  Offset extraoffs;
  void *buf;
  Size buflen;
  ImageioCap iocap;
  ImageioStatus iostat;
};


/* constants */

#define ImageioFormatVersionInitializer  (ImageioFormatVersion){ NULL, 0, 0 }

#define ImageioFormatInitializer  (ImageioFormat){ ImageioFormatVersionInitializer, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0 }

#define ImageioInitializer  (Imageio){ NULL, NULL, 0, 0, NULL, NULL, TypeUndef, ImageAsym, 0, 0, NULL, 0, NULL, 0, NULL, NULL, NULL, NULL, NULL, -1, NULL, 0, 0, 0 }

#define ImageDateTimeSep ". :.2"


/* variables */

extern Size ImageioLoadSize;


/* prototypes */

extern ImageioStatus ImageioGetEndian();

extern void ImageioSetEndian
            (ImageioStatus *iostat,
             ImageioStatus swap);

extern char *ImageioGetVersion
             (const char *txt,
              const char *vers,
              Size *len,
              char *buf);

extern Status ImageioErrFmt
              (Imageio *imageio,
               Status status);

extern Status ImageioImageAlloc
              (Imageio *imageio,
               const Size *len,
               const Index *low);

extern Status ImageioBufAlloc
              (Imageio *imageio,
               Size size);

extern Status ImageioModeInit
              (Imageio *imageio);

extern Status ImageioSizeSet
              (Imageio *imageio,
               Offset *offset,
               Size length,
               Size *size,
               Size *count);

extern Status ImageioMmapSet
              (Imageio *imageio,
               Offset offset,
               Size length,
               void **addr);

extern Status ImageioAmapAddr
              (Imageio *imageio,
               Offset offset,
               Size length,
               void **addr);

extern Status ImageioAmapSync
              (Imageio *imageio);

extern Status ImageioAmapFinal
              (Imageio *imageio);

extern void ImageioCleanup
            (Imageio *imageio);

extern Status ImageioFlip
              (Size length,
               Size elsize,
               void *dst);


#endif
