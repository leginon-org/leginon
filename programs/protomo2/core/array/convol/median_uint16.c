/*----------------------------------------------------------------------------*
*
*  median_uint16.c  -  array: operations for data type uint16
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


#define TYPE     uint16_t
#define TYPEMIN  0
#define TYPEMAX  UINT16_MAX


/* functions */

extern Status FilterMedian2dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr)

#include "median_2d.h"


extern Status FilterMedian3dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr)

#include "median_3d.h"
