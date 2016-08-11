/*----------------------------------------------------------------------------*
*
*  linear_2d_int16_int16.c  -  array: spatial linear transformations
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

extern Status Linear2dInt16Int16
              (const Size *srclen,
               const void *srcaddr,
               const Coord *A,
               const Coord *b,
               const Size *dstlen,
               void *dstaddr,
               const Coord *c,
               const TransformParam *param)

#define SRCTYPE int16_t
#define DSTTYPE int16_t

#define DSTTYPEMIN (INT16_MIN)
#define DSTTYPEMAX (INT16_MAX)

#include "linear_2d.h"
