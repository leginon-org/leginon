/*----------------------------------------------------------------------------*
*
*  sample_3d_uint8_real.c  -  array: sampling
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

extern Status Sample3dUint8Real
              (const Size *srclen,
               const void *srcaddr,
               const Size *smp,
               const Size *b,
               const Size *dstlen,
               void *dstaddr,
               const Size *c,
               const SampleParam *param)

#define SRCTYPE uint8_t
#define DSTTYPE Real

#define DSTTYPEMIN (-RealMax)
#define DSTTYPEMAX (+RealMax)

#include "sample_3d.h"
