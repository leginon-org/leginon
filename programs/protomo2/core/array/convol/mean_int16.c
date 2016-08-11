/*----------------------------------------------------------------------------*
*
*  mean_int16.c  -  array: operations for data type int16
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


#define TYPE     int16_t
#define TYPEMIN  INT16_MIN
#define TYPEMAX  INT16_MAX

#undef FILTERMIN
#undef FILTERMAX
#undef FILTERMEAN

#define FILTERMEAN


/* functions */

extern Status FilterMean2dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_2d.h"


extern Status FilterMean3dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_3d.h"
