/*----------------------------------------------------------------------------*
*
*  sample_2d_uint32_uint32.c  -  array: sampling
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

extern Status Sample2dUint32Uint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *smp,
               const Size *b,
               const Size *dstlen,
               void *dstaddr,
               const Size *c,
               const SampleParam *param)

#define SRCTYPE uint32_t
#define DSTTYPE uint32_t

#define DSTTYPEMIN (0)
#define DSTTYPEMAX (UINT32_MAX)

#include "sample_2d.h"
