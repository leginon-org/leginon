/*----------------------------------------------------------------------------*
*
*  tomoalign.h  -  align: series alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoalign_h_
#define tomoalign_h_

#include "tomoaligndefs.h"
#include "tomowindow.h"
#include "tomodiagn.h"
#include "tomoref.h"
#include "maskparam.h"
#include "spatial.h"
#include <stdio.h>

#define TomoalignName   "tomoalign"
#define TomoalignVers   TOMOALIGNVERS"."TOMOALIGNBUILD
#define TomoalignCopy   TOMOALIGNCOPY


/* exception codes */

enum {
  E_TOMOALIGN = TomoalignModuleCode,
  E_TOMOALIGN_RNG,
  E_TOMOALIGN_MAXCODE
};


/* data structures */

typedef struct {
  Coord step;
  Coord limit;
} TomoalignGrid;

typedef struct {
  const Tomoseries *series;
  Tomowindow *window;
  Tomoimage *image;
  Tomoref *ref;
  Size count;
  Size start;
  Coord maxshift;
  Coord maxcorr;
  Coord transmax;
  Tomodiagn *cor;
  TomoalignGrid grid;
  Tomoflags flags;
  void *final;
  void *data;
} Tomoalign;

typedef struct {
  Size startimage;
  Size *selection;
  Size *exclusion;
  Coord maxangle;
  Coord maxshift;
  Coord maxcorr;
  Coord transmax;
  Coord startangle;
  TomoalignGrid grid;
  TomowindowCorrParam corr;
  Tomoflags flags;
} TomoalignParam;


/* constants */

#define TomoalignGridInitializer  (TomoalignGrid){ 0, 0 }

#define TomoalignInitializer  (Tomoalign){ NULL, NULL, NULL, NULL, 0, 0, 0, 0, -CoordMax, NULL, TomoalignGridInitializer, 0, NULL, NULL }

#define TomoalignParamInitializer  (TomoalignParam){ SizeMax, NULL, NULL, 90.0, 0, 0, CoordMax, -CoordMax, TomoalignGridInitializer, TomowindowCorrParamInitializer, 0 }


/* prototypes */

extern Tomoalign *TomoalignCreate
                  (const Tomoseries *series);

extern Status TomoalignDestroy
              (Tomoalign *align);

extern Status TomoalignInit
              (Tomoalign *align,
               const TomoalignParam *aliparam,
               const TomowindowParam *winparam,
               const TomorefParam *refparam);

extern Status TomoalignFinal
              (Tomoalign *align);

extern Status TomoalignGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomoalignParam *param);

extern Status TomoalignParamFinal
              (TomoalignParam *param);

extern Status TomoalignExec
              (Tomoalign *align);

extern Status TomoalignWrite
              (const Tomoalign *align,
               FILE *stream);

extern Tomotilt *TomoalignTilt
                 (const Tomoalign *align);

extern Tomoalign *TomoalignSeries
                  (Tomoseries *series,
                   const TomoalignParam *aliparam,
                   const TomowindowParam *winparam,
                   const TomorefParam *refparam);

extern Status TomoalignSeriesCorr
              (Tomoseries *series,
               Real *r,
               const TomoalignParam *aliparam,
               const TomowindowParam *winparam,
               const TomorefParam *refparam);


#endif
