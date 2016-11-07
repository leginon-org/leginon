/*----------------------------------------------------------------------------*
*
*  tomoiocommon.h  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoiocommon_h_
#define tomoiocommon_h_

#include "tomoio.h"


/* data structures */

typedef enum {
  TomoioModeUndef,
  TomoioModeImageio,
  TomoioModeMalloc,
} TomoioMode;

struct _Tomoio {
  TomoioMode mode;
  union {
    Imageio *imageio;
    uint8_t *addr;
  } handle;
  IOMode iomode;
  void *addr;
  Offset offs;
  void *metadata;
  I3data extra;
  Coord sampling;
};


/* constants */


#define TomoioInitializer  (Tomoio){ TomoioModeUndef, { NULL }, 0, NULL, 0, NULL, I3dataInitializer, 0 }


/* prototypes */

extern char *TomoioPath
             (const char *path,
              const char *prfx,
              const char *sffx);


#endif
