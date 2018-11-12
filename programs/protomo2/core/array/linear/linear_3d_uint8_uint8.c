/*----------------------------------------------------------------------------*
*
*  linear_3d_uint8_uint8.c  -  array: spatial linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "linear.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Linear3dUint8Uint8
              (const Size *srclen,
               const void *srcaddr,
               const Coord *A,
               const Coord *b,
               const Size *dstlen,
               void *dstaddr,
               const Coord *c,
               const TransformParam *param)

#define SRCTYPE uint8_t
#define DSTTYPE uint8_t

#define DSTTYPEMIN (0)
#define DSTTYPEMAX (UINT8_MAX)

#include "linear_3d.h"
