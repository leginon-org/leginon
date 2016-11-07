/*----------------------------------------------------------------------------*
*
*  fffio.h  -  imageio: FFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fffio_h_
#define fffio_h_

#include "imageio.h"
#include "i3data.h"

#define FFFioName   "fffio"
#define FFFioVers   ImageioVers
#define FFFioCopy   ImageioCopy


/* exception codes */

enum {
  E_FFFIO = FFFioModuleCode,
  E_FFFIO_MAXCODE
};


/* types */

typedef enum {
  T_UNDEF   =  0,
  T_BYTE    =  2,
  T_WORD    =  3,
  T_INT     =  4,
  T_REAL    =  5,
  T_CMPLX   =  6,
  T_LOGIC   =  8,
  T_RGB     = 13,
  T_BYTE_S  = 14,
  T_WORD_U  = 15,
  T_INT_U   = 16,
  T_INT64_U = 17,
  T_INT64_S = 18,
  T_IMAG    = 19,
  T_REAL64  = 20,
  T_IMAG64  = 21,
  T_CMPLX64 = 22,
  T_MAXTYPE
} FFFImagetype;

typedef struct {
  uint8_t magic[16];
  uint16_t kind;
  uint16_t type;
  uint16_t tsize;
  uint16_t dim;
  uint32_t data;
  uint32_t attr;
  char cre[16];
  char mod[16];
} FFFHeader;

typedef struct {
  FFFHeader hdr;
  uint32_t dscrlen;
  uint32_t dscrsize;
  int64_t attr;
  I3data extra;
  Bool i3meta;
} FFFMeta;

#define FFFdscrsize 4

typedef int32_t FFFArrayDscr[FFFdscrsize];

#define FFFlow  0
#define FFFhigh 1
#define FFFlen  2
#define FFFsize 3


/* constants */

#define FFFHeaderSize 64

#define K_NEG       1
#define K_CC        2
#define K_SYM       4
#define K_MOD2      8

#define K_UNDEF     7

#define K_ASYM      0
#define K_REAL      0
#define K_EVEN      K_SYM
#define K_ODD       (K_SYM|K_NEG)
#define K_HERM      (K_SYM|K_CC)
#define K_ANTIHERM  (K_SYM|K_CC|K_NEG)

#define K_HERMEVEN  K_HERM
#define K_HERMODD   (K_HERM|K_MOD2)

#define K_CYCL      0x10
#define K_FOU       0x20

#define K_MASK      0x3f

#define TS_UNDEF    0
#define TS_BYTE     sizeof(uint8_t)
#define TS_WORD     sizeof(int16_t)
#define TS_INT      sizeof(int32_t)
#define TS_REAL     sizeof(Real32)
#define TS_CMPLX    sizeof(Cmplx32)
#define TS_RGB      (3*sizeof(uint8_t))
#define TS_BYTE_S   sizeof(int8_t)
#define TS_WORD_U   sizeof(uint16_t)
#define TS_INT_U    sizeof(uint32_t)
#define TS_INT64_U  sizeof(uint64_t),
#define TS_INT64_S  sizeof(int64_t),
#define TS_IMAG     sizeof(Real32)
#define TS_REAL64   sizeof(Real64),
#define TS_IMAG64   sizeof(Real64)
#define TS_CMPLX64  sizeof(Cmplx64)


/* variables */

extern const uint8_t FFFbigmagic[16];
extern const uint8_t FFFltlmagic[16];


/* prototypes */

extern Status FFFFmt
              (Imageio *imageio);

extern Status FFFNew
              (Imageio *imageio);

extern Status FFFOld
              (Imageio *imageio);

extern Status FFFSiz
              (Imageio *imageio,
               Offset size,
               Size length);

extern Status FFFFin
              (Imageio *imageio);

extern Status FFFExtra
              (Imageio *imageio,
               IOMode mode,
               void *extra);

extern Status FFFGet
              (const Imageio *imageio,
               ImageioMeta *meta);

extern void FFFSetTime
            (const Time *tm,
             char *buf,
             Size len);

extern void FFFMetaInit
            (FFFMeta *meta);

extern Status FFFMetaRead
              (Imageio *imageio,
               FFFMeta *meta);

extern Status FFFMetaWrite
              (Imageio *imageio);


#endif
