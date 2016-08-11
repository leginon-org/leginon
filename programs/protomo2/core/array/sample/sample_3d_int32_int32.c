/*----------------------------------------------------------------------------*
*
*  sample_3d_int32_int32.c  -  array: sampling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "samplecommon.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Sample3dInt32Int32
              (const Size *srclen,
               const void *srcaddr,
               const Size *smp,
               const Size *b,
               const Size *dstlen,
               void *dstaddr,
               const Size *c,
               const SampleParam *param)

#define SRCTYPE int32_t
#define DSTTYPE int32_t

#define DSTTYPEMIN (INT32_MIN)
#define DSTTYPEMAX (INT32_MAX)

#include "sample_3d.h"
