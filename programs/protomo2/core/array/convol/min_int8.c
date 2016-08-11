/*----------------------------------------------------------------------------*
*
*  min_int8.c  -  array: operations for data type int8
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


#define TYPE     int8_t
#define TYPEMIN  INT8_MIN
#define TYPEMAX  INT8_MAX

#undef FILTERMIN
#undef FILTERMAX
#undef FILTERMEAN

#define FILTERMIN


/* functions */

extern Status FilterMin2dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_2d.h"


extern Status FilterMin3dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_3d.h"
