/*----------------------------------------------------------------------------*
*
*  tomoseriesset.h  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoseriesset_h_
#define tomoseriesset_h_

#include "tomoseries.h"


/* prototypes */

extern Status TomoseriesSetSampling
              (const TomoseriesParam *param,
               const char *cacheprfx,
               TomodataParam *datapar,
               Tomoflags *flags,
               Coord *sampling);

extern Status TomoseriesSetParam
              (const TomoseriesParam *param,
               const char *cacheprfx,
               TomodataParam *datapar,
               Tomoseries *series);


#endif
