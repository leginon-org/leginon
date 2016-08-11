/*----------------------------------------------------------------------------*
*
*  polar_3d_int32_int32.c  -  array: spatial polar transformations
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

extern Status Polar3dInt32Int32
              (const Size *srclen,
               const void *srcaddr,
               const Coord *A,
               const Coord *b,
               const Size *dstlen,
               void *dstaddr,
               const Coord *c,
               const TransformParam *param)

#define SRCTYPE int32_t
#define DSTTYPE int32_t

#define DSTTYPEMIN (INT32_MIN)
#define DSTTYPEMAX (INT32_MAX)

#include "polar_3d.h"
