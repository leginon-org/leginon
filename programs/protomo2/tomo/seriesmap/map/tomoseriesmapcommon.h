/*----------------------------------------------------------------------------*
*
*  tomoseriesmapcommon.h  -  series: maps
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoseriesmapcommon_h_
#define tomoseriesmapcommon_h_

#include "tomoseriesmap.h"


/* prototypes */

extern Tomomap *TomoseriesmapCreate
                (const Tomoseries *series,
                 const TomoseriesmapParam *param);

extern Status TomoseriesmapInitBck
              (Tomomap *map,
               const Tomoseries *series);


#endif
