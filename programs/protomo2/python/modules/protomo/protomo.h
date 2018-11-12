/*----------------------------------------------------------------------------*
*
*  protomo.h  -  python tomography extension
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef protomo_h_
#define protomo_h_

#include "tomopy.h"
#include "tomoseries.h"

#define ProtomoName   "protomo"
#define ProtomoVers   TOMOPYVERS"."TOMOPYBUILD
#define ProtomoCopy   TOMOPYCOPY


/* exception codes */

enum {
  E_PROTOMO = ProtomoModuleBase,
  E_PROTOMO_ALI,
  E_PROTOMO_FIT,
  E_PROTOMO_IMG,
  E_PROTOMO_UPD,
  E_PROTOMO_MAXCODE
};

/* types */

typedef struct {
  PyObject_HEAD
  Tomoparam *param;
} ProtomoParam;

typedef struct {
  PyObject_HEAD
  Tomotilt *tilt;
} ProtomoGeom;

typedef struct {
  PyObject_HEAD
  Tomoseries *series;
  Tomogeom *geom;
  Tomotilt *alignd;
  Tomotilt *fitted;
  Tomoparam *param;
  Bool unaligned;
} ProtomoSeries;


/* macros */

#define ProtomoSection "tiltseries"


/* variables */

extern TomoPy *protomo;

extern PyTypeObject *ProtomoParamTypeObject;
extern PyTypeObject *ProtomoGeomTypeObject;
extern PyTypeObject *ProtomoSeriesTypeObject;


/* prototypes */

extern PyMODINIT_FUNC initprotomo();

extern void ProtomoParamInit
            (TomoPy *mod);

extern void ProtomoGeomInit
            (TomoPy *mod);

extern void ProtomoSeriesInit
            (TomoPy *mod);


#endif
