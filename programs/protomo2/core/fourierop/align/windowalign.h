/*----------------------------------------------------------------------------*
*
*  windowalign.h  -  fourierop: window alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef windowalign_h_
#define windowalign_h_

#include "window.h"
#include "windowfourier.h"

#define WindowAlignName   "windowalign"
#define WindowAlignVers   FOURIEROPVERS"."FOURIEROPBUILD
#define WindowAlignCopy   FOURIEROPCOPY


/* exception codes */

enum {
  E_WINDOWALIGN = WindowAlignModuleCode,
  E_WINDOWALIGN_MAXCODE
};


/* types */

typedef struct {
  Window win;
  const MaskParam *winmsk;
  WindowFourier fou;
} WindowAlign;

typedef struct {
  WindowParam win;
  const MaskParam *winmsk;
  WindowFourierParam fou;
  const MaskParam *foumsk;
  const MaskParam *fouflt;
  const PeakParam *pkpar;
} WindowAlignParam;


/* constants */

#define WindowAlignInitializer  (WindowAlign){ WindowInitializer, NULL, WindowFourierInitializer }

#define WindowAlignParamInitializer  (WindowAlignParam){ WindowParamInitializer, NULL, WindowFourierParamInitializer, NULL, NULL, NULL }


/* prototypes */

extern Status WindowAlignInit
              (Size dim,
               const Size *len,
               WindowAlign *align,
               const WindowAlignParam *param);

extern Status WindowAlignFinal
              (WindowAlign *align);

extern Status WindowAlignResample
              (const WindowAlign *align,
               const Size *len,
               Type type,
               const void *addr,
               const Coord *A,
               const Coord *b,
               Real *winaddr,
               Stat *winstat,
               const MaskParam *winmsk);

extern Status WindowAlignTransform
              (const WindowAlign *align,
               Real *winaddr,
               Cmplx *fouaddr,
               Real *foupwr,
               const MaskParam *fouflt);

extern Status WindowAlignCcf
              (const WindowAlign *align,
               const Cmplx *refaddr,
               const Cmplx *fouaddr,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr);

extern Status WindowAlignRef
              (const WindowAlign *align,
               const Size *len,
               Type type,
               const void *addr,
               const Coord *A,
               const Coord *b,
               Real *winaddr,
               const MaskParam *winmsk,
               Cmplx *refaddr,
               Real *refpwr,
               const MaskParam *refflt);

extern Status WindowAlignCorr
              (const WindowAlign *align,
               const Cmplx *refaddr,
               Real refpwr,
               const Cmplx *fouaddr,
               Real *foupwr,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr,
               Real *cornorm,
               Coord *pos,
               Real *pk);

extern Status WindowAlignRegister
              (const WindowAlign *align,
               const Size *len,
               Type type,
               const void *addr,
               const Coord *A,
               const Coord *b,
               Real *winaddr,
               const MaskParam *winmsk,
               const Cmplx *refaddr,
               Real refpwr,
               Cmplx *fouaddr,
               Real *foupwr,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr,
               Real *cornorm,
               Coord *pos,
               Real *pk);


#endif
