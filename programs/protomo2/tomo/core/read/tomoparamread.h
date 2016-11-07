/*----------------------------------------------------------------------------*
*
*  tomoparamread.h  -  core: retrieve parameters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoparamread_h_
#define tomoparamread_h_

#include "tomoparam.h"
#include "tomo.h"
#include "emdefs.h"
#include "ccf.h"
#include "imagectf.h"
#include "imageio.h"
#include "mask.h"
#include "preproc.h"
#include "spatial.h"
#include "transfer.h"
#include "transform.h"
#include "window.h"

#define TomoparamReadName   "tomoparamread"
#define TomoparamReadVers   TOMOVERS"."TOMOBUILD
#define TomoparamReadCopy   TOMOCOPY


/* exception codes */

enum {
  E_TOMOPARAMREAD = TomoparamReadModuleCode,
  E_TOMOPARAMREAD_ERROR,
  E_TOMOPARAMREAD_SEC,
  E_TOMOPARAMREAD_PAR,
  E_TOMOPARAMREAD_VAL,
  E_TOMOPARAMREAD_CONFL,
  E_TOMOPARAMREAD_MAXCODE
};


/* types */

typedef enum {
  TomoparamMaskNormal  = 0x01,
  TomoparamMaskInv     = 0x02,
  TomoparamMaskFourier = 0x04,
} TomoparamMode;


/* prototypes */

extern Status TomoparamReadPush
              (Tomoparam *tomoparam,
               const char *ident,
               const char **sect,
               Bool req);

extern Status TomoparamReadError
              (const char *sect,
               const char *ident,
               Status status);

extern Status TomoparamReadErrorConflict
              (const char *sect,
               const char *ident,
               const char *confl);

extern Status TomoparamEM
              (Tomoparam *tomoparam,
               const char *ident,
               EMparam *emparam);

extern Status TomoparamCCF
              (Tomoparam *tomoparam,
               const char *ident,
               CcfParam *ccfparam);

extern Status TomoparamImageio
              (Tomoparam *tomoparam,
               const char *ident,
               ImageioParam *ioparam);

extern Status TomoparamMask
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               MaskParam *maskparam,
               TomoparamMode mode);

extern Status TomoparamMaskWedge
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               MaskParam *maskparam,
               TomoparamMode mode);

extern Status TomoparamPeak
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               PeakParam *peakparam);

extern Status TomoparamPreproc
              (Tomoparam *tomoparam,
               const char *ident,
               const PreprocParam *paramdefault,
               Size *dimptr,
               PreprocParam *preprocparam);

extern Status TomoparamTransfer
              (Tomoparam *tomoparam,
               const char *ident,
               TransferParam *transferparam);

extern Status TomoparamTransform
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               Transform *transform,
               Bool translation);

extern Status TomoparamTransform2
              (Tomoparam *tomoparam,
               const char *ident,
               Transform *transform);

extern Status TomoparamTransform3
              (Tomoparam *tomoparam,
               const char *ident,
               Transform *transform);

extern Status TomoparamWindow
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               Size *len,
               WindowParam *windowparam);

extern Status TomoparamImageioFinal
              (ImageioParam *ioparam);

extern Status TomoparamMaskFinal
              (MaskParam *maskparam);

extern Status TomoparamMaskParamFinal
              (MaskParam *maskparam);

extern Status TomoparamPeakFinal
              (PeakParam *peakparam);

extern Status TomoparamPreprocFinal
              (PreprocParam *preprocparam);

extern Status TomoparamTransformFinal
              (Transform *transform);

extern Status TomoparamWindowFinal
              (WindowParam *windowparam);


#endif
