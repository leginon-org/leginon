/*----------------------------------------------------------------------------*
*
*  max_int32.c  -  array: operations for data type int32
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


#define TYPE     int32_t
#define TYPEMIN  INT32_MIN
#define TYPEMAX  INT32_MAX

#undef FILTERMIN
#undef FILTERMAX
#undef FILTERMEAN

#define FILTERMAX


/* functions */

extern Status FilterMax2dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_2d.h"


extern Status FilterMax3dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_3d.h"
