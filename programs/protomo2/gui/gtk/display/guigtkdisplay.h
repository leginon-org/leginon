/*----------------------------------------------------------------------------*
*
*  guigtkdisplay.h  -  guigtk: EM image viewer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef guigtkdisplay_h_
#define guigtkdisplay_h_

#include "guigtkdefs.h"
#include "imageio.h"

#define GuigtkDisplayName   "guigtkdisplay"
#define GuigtkDisplayVers   GUIGTKVERS"."GUIGTKBUILD
#define GuigtkDisplayCopy   GUIGTKCOPY


/* exception codes */

enum {
  E_GUIGTKDISPLAY = GuigtkDisplayModuleCode,
  E_GUIGTKDISPLAY_MAXCODE
};


/* data structures */

typedef enum {
  GuigtkDisplayRe,
  GuigtkDisplayIm,
  GuigtkDisplayAbs,
  GuigtkDisplayLogAbs,
  GuigtkDisplayFuncMax,
} GuigtkDisplayFunc;

typedef enum {
  GuigtkDisplayLogging = 0x01,
  GuigtkDisplayDetach = 0x02,
} GuigtkDisplayFlags;

typedef struct {
  Size dim;
  Size count;
  Coord *pos;
  Coord *rot;
} GuigtkDisplayTransf;

typedef struct {
  Coord zoom;
  Coord range[2];
  GuigtkDisplayFunc func;
  GuigtkDisplayFlags flags;
  const ImageioParam *iopar;
} GuigtkDisplayParam;


/* constants */

#define GuigtkDisplayParamInitializer  (GuigtkDisplayParam){ 1, { CoordMax, 0 }, GuigtkDisplayFuncMax, 0, NULL }


/* variables */

extern const char *GuigtkDisplayVersion;

extern const char *GuigtkDisplayCopyright;


/* prototypes */

extern Status GuigtkDisplayCreate
              (const Image *image,
               const void *addr,
               const GuigtkDisplayParam *param);

extern Status GuigtkDisplayCreateTransf
              (const Image *image,
               const void *addr,
               const GuigtkDisplayTransf *in,
               GuigtkDisplayTransf *out,
               const GuigtkDisplayParam *param);

extern Status GuigtkDisplayCreateFile
              (const char *path,
               const char *posin,
               const char *posout,
               const GuigtkDisplayParam *param);


#endif
