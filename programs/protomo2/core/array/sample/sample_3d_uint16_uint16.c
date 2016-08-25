/*----------------------------------------------------------------------------*
*
*  sample_3d_uint16_uint16.c  -  array: sampling
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

extern Status Sample3dUint16Uint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *smp,
               const Size *b,
               const Size *dstlen,
               void *dstaddr,
               const Size *c,
               const SampleParam *param)

#define SRCTYPE uint16_t
#define DSTTYPE uint16_t

#define DSTTYPEMIN (0)
#define DSTTYPEMAX (UINT16_MAX)

#include "sample_3d.h"
