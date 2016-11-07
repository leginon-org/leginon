/*----------------------------------------------------------------------------*
*
*  imagicio.h  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagicio_h_
#define imagicio_h_

#include "imagiciodefs.h"
#include "imageio.h"
#include "fileio.h"

#define ImagicioName   "imagicio"
#define ImagicioVers   ImageioVers
#define ImagicioCopy   ImageioCopy


/* exception codes */

enum {
  E_IMAGICIO = ImagicioModuleCode,
  E_IMAGICIO_NAME,
  E_IMAGICIO_FEAT,
  E_IMAGICIO_FLOAT,
  E_IMAGICIO_ALLOC,
  E_IMAGICIO_MAXCODE
};


/* config */

#define ImagicImageMaxDim  4


/* Imagic data types */

typedef struct {
  const char *name;
  Type type;
  ImageAttr attr;
} ImagicType;


/* types */

typedef struct {
  ImagicHeader header;
  Fileio *hdrfile;
  Time cre;
  Size ifol;
  Size  len[ImagicImageMaxDim];
  Index low[ImagicImageMaxDim];
} ImagicMeta;


/* prototypes */

extern Status ImagicFmt
              (Imageio *imageio);

extern Status ImagicNew
              (Imageio *imageio);

extern Status ImagicOld
              (Imageio *imageio);

extern Status ImagicSiz
              (Imageio *imageio,
               Offset size,
               Size length);

extern Status ImagicExtra
              (Imageio *imageio,
               IOMode mode,
               void *extra);

extern Status ImagicFin
              (Imageio *imageio);

extern Status ImagicGet
              (const Imageio *imageio,
               ImageioMeta *meta);

extern Status ImagicImageFileOpen
              (Imageio *imageio);

extern Status ImagicGetType
              (const ImagicHeader *hdr,
               Type *type,
               ImageAttr *attr);

extern Status ImagicSetType
              (Type type,
               ImageAttr attr,
               ImagicHeader *hdr);

extern Status ImagicHeaderRead
              (Imageio *imageio,
               ImagicHeader *hdr);

extern Status ImagicHeaderWrite
              (Imageio *imageio);


#endif
