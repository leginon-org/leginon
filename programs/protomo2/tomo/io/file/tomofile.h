/*----------------------------------------------------------------------------*
*
*  tomofile.h  -  series: tilt series image file handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomofile_h_
#define tomofile_h_

#include "tomoiodefs.h"
#include "tomotilt.h"
#include "imageio.h"

#define TomofileName   "tomofile"
#define TomofileVers   TOMOIOVERS"."TOMOIOBUILD
#define TomofileCopy   TOMOIOCOPY


/* exception codes */

enum {
  E_TOMOFILE = TomofileModuleCode,
  E_TOMOFILE_OPEN,
  E_TOMOFILE_DIM,
  E_TOMOFILE_MOD,
  E_TOMOFILE_MAXCODE
};


/* data structures */

typedef struct {
  uint32_t nameindex;
  uint32_t dim;
  uint32_t len[3];
  int32_t low[3];
  uint32_t type;
  uint32_t attr;
  uint8_t checksum[64];
} TomofileDscr;

typedef struct {
  const char *name;
  const char *path;
  Imageio *handle;
} TomofileIO;

typedef struct {
  Size files;
  TomofileDscr *dscr;
  TomofileIO *io;
  Size strings;
  const char *string;
  int width;
  Tomoflags flags;
} Tomofile;

typedef struct {
  const char *pathlist;
  const char *imgsffx;
  const char *format;
  ImageioCap cap;
  Tomoflags flags;
} TomofileParam;


/* constants */

#define TomofileInitializer  (Tomofile){ 0, NULL, NULL, 0, NULL, 0, 0 }

#define TomofileParamInitializer  (TomofileParam){ NULL, NULL, NULL, ImageioParamDefault.cap, 0 }


/* prototypes */

extern Tomofile *TomofileCreate
                 (const Tomotilt *tomotilt);

extern Status TomofileInit
              (Tomofile *tomofile,
               const TomofileParam *param);

extern Status TomofileFinal
              (Tomofile *tomofile);

extern Status TomofileDestroy
              (Tomofile *tomofile);


#endif
