/*----------------------------------------------------------------------------*
*
*  max_uint8.c  -  array: operations for data type uint8
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

#undef FILTERMIN
#undef FILTERMAX
#undef FILTERMEAN

#define FILTERMAX


/* functions */

extern Status FilterMax2dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_2d.h"


extern Status FilterMax3dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_3d.h"
