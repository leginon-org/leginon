/*----------------------------------------------------------------------------*
*
*  tomotiltfit.h  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomotiltfit_h_
#define tomotiltfit_h_

#define TomoTiltFitName   "tomotiltfit"
#define TomoTiltFitVers   TOMOFITVERS"."TOMOFITBUILD
#define TomoTiltFitCopy   TOMOFITCOPY

#include "tomofitdefs.h"
#include "tomotilt.h"
#include "tomogeom.h"
#include "tomoparam.h"


/* constants */

#define TomotiltFitEuler    0x1000

#define TomotiltFitAzim     0x0100
#define TomotiltFitElev     0x0200
#define TomotiltFitOffs     0x0400

#define TomotiltFitOrient   0x0010

#define TomotiltFitTheta    0x0004
#define TomotiltFitAlpha    0x0002
#define TomotiltFitScale    0x0001

#define TomotiltFitMask     0x0ffff

#define TomotiltFitLog      0x10000
#define TomotiltFitDat      0x20000
#define TomotiltFitDbg      0x40000
#define TomotiltFitDet      0x80000


/* exception codes */

enum {
  E_TOMOTILTFIT = TomotiltFitModuleCode,
  E_TOMOTILTFIT_NONE,
  E_TOMOTILTFIT_REF,
  E_TOMOTILTFIT_IMG,
  E_TOMOTILTFIT_PARAM,
  E_TOMOTILTFIT_DATA,
  E_TOMOTILTFIT_FIT,
  E_TOMOTILTFIT_CORR,
  E_TOMOTILTFIT_MAXCODE
};


/* types */

typedef struct {
  Coord corr[2];
  Coord beta;
} TomotiltFitResid;

typedef struct {
  Size *selection;
  Size *exclusion;
  TomotiltFitResid *resid;
  int flags;
} TomotiltFitParam;


/* constants */

#define TomotiltFitParamInitializer  (TomotiltFitParam){ NULL, NULL, NULL, 0 }


/* prototypes */

extern Tomotilt *TomotiltFit
                 (const Tomotilt *tomotilt,
                  const Tomogeom *tomogeom,
                  const TomotiltFitParam *param);

extern Status TomotiltFitGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomotiltFitParam *fitparam);

extern Status TomotiltFitParamFinal
              (TomotiltFitParam *fitparam);


#endif
