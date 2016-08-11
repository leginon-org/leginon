/*----------------------------------------------------------------------------*
*
*  tomocache.h  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomocache_h_
#define tomocache_h_

#include "tomoseriesdefs.h"
#include "image.h"
#include "i3io.h"

#define TomocacheName   "tomocache"
#define TomocacheVers   TOMOSERIESVERS"."TOMOSERIESBUILD
#define TomocacheCopy   TOMOSERIESCOPY


/* exception codes */

enum {
  E_TOMOCACHE = TomocacheModuleCode,
  E_TOMOCACHE_FMT,
  E_TOMOCACHE_MAXCODE
};


/* data structures */

typedef struct {
  uint32_t number;
  uint32_t len[2];
  int32_t low[2];
  uint32_t type;
  uint32_t attr;
  char checksum[64];
} TomocacheDscr;

typedef struct {
  Size images;
  I3io *handle;
  TomocacheDscr *dscr;
  Size sampling;
  Bool preproc;
  Bool new;
} Tomocache;


/* prototypes */

extern Tomocache *TomocacheCreate
                  (const char *path,
                   Size images,
                   Size sampling,
                   Tomoflags flags);

extern Status TomocacheDestroy
              (Tomocache *cache,
               Status fail);

extern Tomocache *TomocacheOpen
                  (const char *path);

extern Status TomocacheGetImage
              (const Tomocache *cache,
               const Size index,
               const Size number,
               Image *img);


#endif
