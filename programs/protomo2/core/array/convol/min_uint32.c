/*----------------------------------------------------------------------------*
*
*  min_uint32.c  -  array: operations for data type uint32
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

#undef FILTERMIN
#undef FILTERMAX
#undef FILTERMEAN

#define FILTERMIN


/* functions */

extern Status FilterMin2dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_2d.h"


extern Status FilterMin3dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_3d.h"
