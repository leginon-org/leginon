/*----------------------------------------------------------------------------*
*
*  median_uint8.c  -  array: operations for data type uint8
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "convol.h"
#include "exception.h"


#define TYPE     uint8_t
#define TYPEMIN  0
#define TYPEMAX  UINT8_MAX


/* functions */

extern Status FilterMedian2dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr)

#include "median_2d.h"


extern Status FilterMedian3dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr)

#include "median_3d.h"
