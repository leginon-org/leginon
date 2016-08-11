/*----------------------------------------------------------------------------*
*
*  tomodatacommon.h  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomodatacommon_h_
#define tomodatacommon_h_

#include "tomodata.h"


/* prototypes */

extern TomodataDscr *TomodataDscrCreate
                     (const Tomodata *data);

extern Status TomodataDscrCache
              (const Tomocache *cache,
               TomodataDscr *dscr);

extern Status TomodataDscrCheck
              (const Tomocache *cache,
               const TomodataDscr *dscr);

extern Status TomodataPreproc
              (const Tomodata *data,
               const Tomocache *iocache,
               TomodataDscr *iodscr,
               Tomocache *cache);

extern Status TomodataSample
              (const Tomodata *data,
               const Tomocache *iocache,
               TomodataDscr *iodscr,
               Tomocache *cache,
               Size sampling);


#endif
