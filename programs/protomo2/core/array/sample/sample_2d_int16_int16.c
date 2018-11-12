/*----------------------------------------------------------------------------*
*
*  sample_2d_int16_int16.c  -  array: sampling
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

extern Status Sample2dInt16Int16
              (const Size *srclen,
               const void *srcaddr,
               const Size *smp,
               const Size *b,
               const Size *dstlen,
               void *dstaddr,
               const Size *c,
               const SampleParam *param)

#define SRCTYPE int16_t
#define DSTTYPE int16_t

#define DSTTYPEMIN (INT16_MIN)
#define DSTTYPEMAX (INT16_MAX)

#include "sample_2d.h"
