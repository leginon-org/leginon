/*----------------------------------------------------------------------------*
*
*  convol_uint32.c  -  array: operations for data type uint32
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


#define TYPE     uint32_t
#define TYPEMIN  0
#define TYPEMAX  UINT32_MAX


/* functions */

extern Status Convol2dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr)

#include "convol_2d.h"


extern Status Convol3dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr)

#include "convol_3d.h"
