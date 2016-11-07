/*----------------------------------------------------------------------------*
*
*  tomoseriescommon.h  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoseriescommon_h_
#define tomoseriescommon_h_

#include "tomoseries.h"


/* prototypes */

extern char *TomoseriesPrfx
             (const TomoseriesParam *param,
              const char *metapath,
              const char *tiltpath);

extern char *TomoseriesOutPrfx
             (const char *prfx,
              const char *outdir);

extern char *TomoseriesCachePrfx
             (const char *prfx,
              const char *cacheprfx,
              const char *cachedir);


#endif
