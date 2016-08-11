/*----------------------------------------------------------------------------*
*
*  polar_2d_int16_real.c  -  array: spatial polar transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "polar.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Polar2dInt16Real
              (const Size *srclen,
               const void *srcaddr,
               const Coord *A,
               const Coord *b,
               const Size *dstlen,
               void *dstaddr,
               const Coord *c,
               const TransformParam *param)

#define SRCTYPE int16_t
#define DSTTYPE Real

#define DSTTYPEMIN (-RealMax)
#define DSTTYPEMAX (+RealMax)

#include "polar_2d.h"
