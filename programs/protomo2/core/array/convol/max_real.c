/*----------------------------------------------------------------------------*
*
*  max_real.c  -  array: operations for data type Real
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


#define TYPE     Real
#define TYPEMIN  (-RealMax)
#define TYPEMAX  (+RealMax)

#undef FILTERMIN
#undef FILTERMAX
#undef FILTERMEAN

#define FILTERMAX


/* functions */

extern Status FilterMax2dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_2d.h"


extern Status FilterMax3dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

#include "minmaxmean_3d.h"
