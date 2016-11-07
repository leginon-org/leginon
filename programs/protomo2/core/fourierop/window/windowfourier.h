/*----------------------------------------------------------------------------*
*
*  windowfourier.h  -  window: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef windowfourier_h_
#define windowfourier_h_

#include "fourieropdefs.h"
#include "fourier.h"
#include "image.h"
#include "mask.h"
#include "ccf.h"
#include "spatial.h"

#define WindowFourierName   "windowfourier"
#define WindowFourierVers   FOURIEROPVERS"."FOURIEROPBUILD
#define WindowFourierCopy   FOURIEROPCOPY


/* exception codes */

enum {
  E_WINDOWFOURIER = WindowFourierModuleCode,
  E_WINDOWFOURIER_MAXCODE
};


/* data structures */

typedef struct {
  Image img;
  Image fou;
  Size fousize;
  Fourier *forw;
  Fourier *back;
  CCMode mode;
  const MaskParam *msk;
  const MaskParam *flt;
  const PeakParam *pkpar;
} WindowFourier;

typedef struct {
  FourierOpt opt;
  CCMode mode;
  Bool mskdefault;
  Bool fltdefault;
  Bool forw;
  Bool back;
} WindowFourierParam;


/* constants */

#define WindowFourierInitializer  (WindowFourier){ ImageInitializer, ImageInitializer, 0, NULL, NULL, CC_XCF, NULL, NULL, NULL }

#define WindowFourierParamInitializer  (WindowFourierParam){ 0, CC_XCF, False, False, True, True }


/* macros */

#define WindowFourierAlloc( w )  ( (Cmplx *)malloc( (w)->fousize * sizeof(Cmplx) ) )


/* prototypes */

extern Status WindowFourierInit
              (Size dim,
               const Size *len,
               const MaskParam *msk,
               const MaskParam *flt,
               const PeakParam *pkpar,
               WindowFourier *win,
               const WindowFourierParam *param);

extern Status WindowFourierFinal
              (WindowFourier *win);

extern Status WindowFourierPower
              (const WindowFourier *win,
               const Cmplx *fouaddr,
               Real *foupwr);

extern Status WindowTransform
              (const WindowFourier *win,
               const Real *imgaddr,
               Cmplx *fouaddr,
               Real *foupwr,
               const MaskParam *fouflt);

extern Status WindowTransformTrf
              (const WindowFourier *win,
               const Real *imgaddr,
               const Coord *A,
               Cmplx *fouaddr,
               Real *foupwr,
               const MaskParam *fouflt);

extern Status WindowCcf
              (const WindowFourier *win,
               const Cmplx *refaddr,
               const Cmplx *fouaddr,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr);

extern Status WindowCcfWgt
              (const WindowFourier *win,
               const Cmplx *refaddr,
               const Real *refwgt,
               const Cmplx *fouaddr,
               Real *fouwgt,
               Status (*wgtfn)(const void *, Size, Real *),
               void *wgtdat,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr);

extern Status WindowPeak
              (const WindowFourier *win,
               const Real *addr,
               Coord *pos,
               Real *pk);


#endif
