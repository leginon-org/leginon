/*----------------------------------------------------------------------------*
*
*  tomoseriesmap.h  -  series: maps
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoseriesmap_h_
#define tomoseriesmap_h_

#include "tomoseriesmapdefs.h"
#include "tomoseries.h"
#include "tomomap.h"

#define TomoseriesmapName   "tomoseriesmap"
#define TomoseriesmapVers   TOMOSERIESMAPVERS"."TOMOSERIESMAPBUILD
#define TomoseriesmapCopy   TOMOSERIESMAPCOPY


/* exception codes */

enum {
  E_TOMOSERIESMAP = TomoseriesmapModuleCode,
  E_TOMOSERIESMAP_MAXCODE
};


/* data structures */

typedef struct {
  Size len[3];
  Coord sampling;
  Coord area;
  Size *selection;
  Size *exclusion;
  TomomapMode mode;
  Coord diam[2];
  Coord apod[2];
  Tomoflags flags;
} TomoseriesmapParam;


/* constants */

#define TomoseriesmapParamInitializer  (TomoseriesmapParam){ { 0, 0, 0 }, 0, 0.95, NULL, NULL, TomomapModeInitializer, { 0, 0 }, { 0, 0 }, 0 }


/* prototypes */

extern Real *TomoseriesmapMem
             (const Tomoseries *series,
              const TomoseriesmapParam *param);

extern Status TomoseriesmapFile
              (const char *path,
               const char *fmt,
               const Tomoseries *series,
               const TomoseriesmapParam *param);

extern Status TomoseriesmapGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               const TomoseriesParam *seriesparam,
               TomoseriesmapParam *mapparam);

extern Status TomoseriesmapParamFinal
              (TomoseriesmapParam *mapparam);


#endif
