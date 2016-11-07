/*----------------------------------------------------------------------------*
*
*  tomomapcommon.h  -  map: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomomapcommon_h_
#define tomomapcommon_h_

#include "tomomap.h"
#include "tomoio.h"


/* data structures */

struct _Tomomap {
  const char *prfx;
  Size count;
  uint8_t *selected;
  Tomoproj *proj;
  Coord sampling;
  TomomapMode mode;
  union {
    Tomotransfer *trans;
  } data;
  Coord diam[2];
  Coord apod[2];
  Tomoflags flags;
};

struct _Tomocomp {
  Tomomap *map;
  Image image;
  Size len[3];
  Index low[3];
  Real *addr;
  Tomoio *handle;
};


/* constants */

#define TomomapInitializer  (Tomomap){ NULL, 0, NULL, NULL, 0, TomomapModeInitializer, { NULL }, { 0, 0 }, { 0, 0 }, 0 }

#define TomocompInitializer  (Tomocomp){ NULL, ImageInitializer, { 0, 0, 0 }, { 0, 0, 0 }, NULL, NULL }


/* prototypes */


#endif
