/*----------------------------------------------------------------------------*
*
*  preproc.h  -  image: preprocessing
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef preproc_h_
#define preproc_h_

#include "arraydefs.h"

#define PreprocName   "preproc"
#define PreprocVers   ARRAYVERS"."ARRAYBUILD
#define PreprocCopy   ARRAYCOPY


/* exception codes */

enum {
  E_PREPROC = PreprocModuleCode,
  E_PREPROC_DIM,
  E_PREPROC_TYPE,
  E_PREPROC_MAXCODE
};


/* types */

typedef enum {
  PreprocUndef,
  PreprocMin,
  PreprocMax,
  PreprocMean,
  PreprocMedian,
  PreprocGauss,
  PreprocFunc = 0x00f,
  PreprocGrad = 0x010,
  PreprocIter = 0x020,
  PreprocClip = 0x040,
  PreprocThr  = 0x080,
  PreprocMsk  = 0x100,
  PreprocBin  = 0x200,
  PreprocLog  = 0x800,
} PreprocFlags;


typedef struct {
  const Size *kernel;
  const Coord *rad;
  Coord thrmin;
  Coord thrmax;
  Coord clipmin;
  Coord clipmax;
  Size grow;
  const char *msg;
  PreprocFlags flags;
} PreprocParam;


/* constants */

#define PreprocParamInitializer  (PreprocParam){ NULL, NULL, 0, 0, 0, 0, 0, NULL, 0 }


/* prototypes */

extern Status Preproc
              (Size dim,
               Type srctype,
               const Size *srclen,
               const void *srcaddr,
               Type msktype,
               const void *mskaddr,
               const Size *statori,
               const Size *statlen,
               Type dsttype,
               const Size *dstori,
               const Size *dstlen,
               void *dstaddr,
               const PreprocParam *param);

extern Status PreprocBinary
              (Size dim,
               Type srctype,
               const Size *srclen,
               const void *srcaddr,
               const Size *statori,
               const Size *statlen,
               const Size *dstori,
               const Size *dstlen,
               uint8_t *dstaddr,
               const PreprocParam *param);


#endif
