/*----------------------------------------------------------------------------*
*
*  tomogeom.h  -  tomography: tilt geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomogeom_h_
#define tomogeom_h_

#include "tomotilt.h"

#define TomogeomName   "tomogeom"
#define TomogeomVers   TOMOVERS"."TOMOBUILD
#define TomogeomCopy   TOMOCOPY


/* exception codes */

enum {
  E_TOMOGEOM = TomogeomModuleCode,
  E_TOMOGEOM_AREA,
  E_TOMOGEOM_MAXCODE
};


/* data structures */

typedef struct {
  Coord A[3][3];
  Coord Am[3][3];
  Coord Af[2][2];
  Coord Ap[3][2];
  Coord Aa[3][2];
  Coord origin[3];
} Tomogeom;


/* prototypes */

extern Status TomogeomInit
              (const Tomotilt *tilt,
               Coord A[3][3],
               const Coord b[3],
               Tomogeom *geom);

extern Status TomogeomLoad
              (const Tomotilt *tilt,
               Size index,
               Coord A[3][3],
               const Coord b[3],
               Tomogeom *geom);

extern Status TomogeomSave
              (Coord A[3][3],
               Coord Am[3][3],
               Coord Ap[3][2],
               Coord origin[3],
               Bool fulltransf,
               Size index,
               Tomotilt *tilt);

extern Status TomogeomCorr
              (Coord Am[3][3],
               Coord Ap[3][2],
               Coord *alpha,
               Coord corr[2],
               Coord *beta);

extern Status TomogeomRot
              (Coord Am[3][3],
               Coord Ap[3][2],
               Coord *alpha);

extern Status TomogeomAreaMax
              (Size nx,
               Size ny,
               Size nz,
               Coord A[3][3],
               Coord a[2],
               Size *len,
               Size *ori,
               Size *size);


#endif
