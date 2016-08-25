/*----------------------------------------------------------------------------*
*
*  tomowindow.h  -  align: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomowindow_h_
#define tomowindow_h_

#include "tomoaligndefs.h"
#include "tomoparam.h"
#include "window.h"
#include "windowfourier.h"

#define TomowindowName   "tomowindow"
#define TomowindowVers   TOMOALIGNVERS"."TOMOALIGNBUILD
#define TomowindowCopy   TOMOALIGNCOPY


/* exception codes */

enum {
  E_TOMOWINDOW = TomowindowModuleCode,
  E_TOMOWINDOW_SIZE,
  E_TOMOWINDOW_MAXCODE
};


/* data structures */

typedef struct {
  Window img;
  WindowFourier fou;
  Window win;
  const MaskParam *winmsk;
  Size corlen[2];
  Size cormed;
  Size corflt;
} Tomowindow;

typedef struct {
  Size len[2];
  Coord area;
  MaskParam *msk;
  MaskParam *flt;
} TomowindowParam;

typedef struct {
  Coord area;
  MaskParam *msk;
  PeakParam *pk;
  CCMode ccmode;
  Size corlen[2];
  Size cormed;
  Size corflt;
} TomowindowCorrParam;


/* constants */

#define TomowindowInitializer  (Tomowindow){ WindowInitializer, WindowFourierInitializer, WindowInitializer, NULL, { 0, 0 }, 0, 0 }

#define TomowindowParamInitializer  (TomowindowParam){ { 0, 0 }, 0, NULL, NULL }

#define TomowindowCorrParamInitializer  (TomowindowCorrParam){ 0.95, NULL, NULL, CC_UNDEF, { 0, 0 }, 0, 0 }


/* prototypes */

extern Tomowindow *TomowindowCreate
                   (const TomowindowParam *param);

extern Status TomowindowCorrInit
              (Tomowindow *window,
               const TomowindowCorrParam *param);

extern Status TomowindowDestroy
              (Tomowindow *window);

extern Status TomowindowCorr
              (const Tomowindow *window,
               const Cmplx *refaddr,
               Real refpwr,
               const Cmplx *fouaddr,
               const Real *foupwr,
               Cmplx *ccfaddr,
               Real *coraddr,
               Real *cornorm,
               Coord *pos,
               Real *pk);

extern Status TomowindowCorrFlt
              (const Size dim,
               const Size *len,
               const Coord *pos,
               Real *addr,
               Size krn);

extern Status TomowindowCorrMedian
              (const Size dim,
               const Size *len,
               Real *addr,
               Real *temp,
               Size krn);

extern Status TomowindowGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomowindowParam *tomowindowparam);

extern Status TomowindowCorrGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomowindowCorrParam *tomowindowcorrparam);

extern Status TomowindowParamFinal
              (TomowindowParam *tomowindowparam);

extern Status TomowindowCorrParamFinal
              (TomowindowCorrParam *tomowindowcorrparam);


#endif
