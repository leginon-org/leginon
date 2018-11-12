/*----------------------------------------------------------------------------*
*
*  tomobackproj.h  -  map: weighted backprojection
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomobackproj_h_
#define tomobackproj_h_

#include "tomomap.h"

#define TomobackprojName   "tomobackproj"
#define TomobackprojVers   TOMOMAPVERS"."TOMOMAPBUILD
#define TomobackprojCopy   TOMOMAPCOPY


/* exception codes */

enum {
  E_TOMOBACKPROJ = TomobackprojModuleCode,
  E_TOMOBACKPROJ_CLIP,
  E_TOMOBACKPROJ_MAXCODE
};


/* prototypes */

extern Status TomobackprojInit
              (Tomomap *map);

extern Status TomobackprojFinal
              (Tomomap *map);

extern Tomotransfer *TomobackprojGetTransfer
                     (Tomomap *map);

extern Status TomobackprojTransfer
              (Tomomap *map,
               Real **transfer);

extern Status TomobackprojWeight
              (Tomomap *map,
               Real **transfer);

extern Status TomobackprojSum
              (Tomocomp *comp);


#endif
