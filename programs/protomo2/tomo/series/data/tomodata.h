/*----------------------------------------------------------------------------*
*
*  tomodata.h  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomodata_h_
#define tomodata_h_

#include "tomocache.h"
#include "tomofile.h"
#include "preproc.h"

#define TomodataName   "tomodata"
#define TomodataVers   TOMOSERIESVERS"."TOMOSERIESBUILD
#define TomodataCopy   TOMOSERIESCOPY


/* exception codes */

enum {
  E_TOMODATA = TomodataModuleCode,
  E_TOMODATA_INDX,
  E_TOMODATA_DIM,
  E_TOMODATA_TYP,
  E_TOMODATA_SMP,
  E_TOMODATA_MOD,
  E_TOMODATA_MAXCODE
};


/* data structures */

typedef struct {
  Size number;
  void *handle;
  Image img;
  Index low[2];
  Size len[2];
  Size size;
  Offset offs;
  char checksum[64];
  Size sampling;
  Coord B1[3][2];
} TomodataDscr;

typedef struct {
  PreprocParam main;
  PreprocParam mask;
  Size border;
} Tomodatapreproc;

typedef struct {
  Size images;
  TomodataDscr *dscr;
  TomotiltImage *image;
  Tomofile *file;
  Tomocache *cache;
  Size sampling;
  const Tomodatapreproc *preproc;
  Tomoflags flags;
} Tomodata;

typedef struct {
  const char *cacheprfx;
  const char *pathlist;
  const char *imgsffx;
  const char *format;
  ImageioCap cap;
  const Tomodatapreproc *preproc;
  Size sampling;
  Tomoflags flags;
} TomodataParam;


/* constants */

#define TomodataInitializer  (Tomodata){ 0, NULL, NULL, NULL, NULL, 0, NULL, 0 }

#define TomodatapreprocInitializer  (Tomodatapreproc){ PreprocParamInitializer, PreprocParamInitializer, 0 }

#define TomodataParamInitializer  (TomodataParam){ NULL, NULL, NULL, NULL, 0, NULL, 0, 0 }


/* prototypes */

extern Tomodata *TomodataCreate
                 (Tomotilt *tilt,
                  Tomofile *file);

extern Status TomodataDestroy
              (Tomodata *data,
               Status fail);

extern Status TomodataInit
              (Tomodata *data,
               const TomodataParam *param);

extern Status TomodataFinal
              (Tomodata *data,
               Status fail);

extern Status TomodataDir
              (char *path);

extern void *TomodataBeginRead
             (const Tomocache *cache,
              const TomodataDscr *dscr,
              const Size index);

extern Status TomodataEndRead
              (const Tomocache *cache,
               const TomodataDscr *dscr,
               const Size index,
               void *addr);

extern Status TomodataDscrFile
              (const Tomodata *data,
               TomodataDscr *dscr);

extern Status TomodataPreprocImage
              (const Tomodata *data,
               const TomodataDscr *dscr,
               const void *srcaddr,
               void *dstaddr,
               uint8_t **mskaddr);

extern void TomodataLogString
            (const Tomodata *data,
             const TomodataDscr *dscr,
             Size index,
             char *buf,
             Size buflen);

extern void TomodataErrString
            (const TomodataDscr *dscr,
             Size index,
             char *buf,
             Size buflen);


#endif
