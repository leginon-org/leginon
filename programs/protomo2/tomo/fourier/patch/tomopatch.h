/*----------------------------------------------------------------------------*
*
*  tomopatch.h  -  fourier: patch
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomopatch_h_
#define tomopatch_h_

#include "tomofourierdefs.h"
#include "tomoseries.h"

#define TomopatchName   "tomopatch"
#define TomopatchVers   TOMOFOURIERVERS"."TOMOFOURIERBUILD
#define TomopatchCopy   TOMOFOURIERCOPY


/* exception codes */

enum {
  E_TOMOPATCH = TomopatchModuleCode,
  E_TOMOPATCH_MAXCODE
};


/* data structures */

typedef struct {
  Size len[2];
  Size inc[2];
  Index minx;
  Index miny;
  Index maxx;
  Index maxy;
  Coord area;
  MaskParam *msk;
  Bool extend;
  Bool complx;
} TomopatchParam;


/* constants */

#define TomopatchParamInitializer  (TomopatchParam){ { 0, 0 }, { 0, 0 }, IndexMin, IndexMin, IndexMax, IndexMax, 0.95, NULL, False, False  }


/* prototypes */

extern Status TomopatchGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomopatchParam *patchparam);

extern Status TomopatchParamFinal
              (TomopatchParam *patchparam);

extern Status TomopatchWrite
              (const Tomoseries *series,
               const char *path,
               const TomopatchParam *param);


#endif
