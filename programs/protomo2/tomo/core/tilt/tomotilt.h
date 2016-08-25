/*----------------------------------------------------------------------------*
*
*  tomotilt.h  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomotilt_h_
#define tomotilt_h_

#include "tomodefs.h"
#include "emdefs.h"
#include <stdio.h>

#define TomotiltName   "tomotilt"
#define TomotiltVers   TOMOVERS"."TOMOBUILD
#define TomotiltCopy   TOMOCOPY


/* exception codes */

enum {
  E_TOMOTILT=TomotiltModuleCode,
  E_TOMOTILT_INT,
  E_TOMOTILT_REAL,
  E_TOMOTILT_AXIS,
  E_TOMOTILT_ORIENT,
  E_TOMOTILT_IMAGE,
  E_TOMOTILT_DEF,
  E_TOMOTILT_REDEF,
  E_TOMOTILT_VAL,
  E_TOMOTILT_FILE,
  E_TOMOTILT_OFFS,
  E_TOMOTILT_EMPTY,
  E_TOMOTILT_EMPARAM,
  E_TOMOTILT_PIXEL,
  E_TOMOTILT_DEFOC,
  E_TOMOTILT_THETA,
  E_TOMOTILT_ORIGIN,
  E_TOMOTILT_PARSE,
  E_TOMOTILT_MAXCODE
};


/* data structures */

typedef struct {
  uint32_t version;
  uint32_t cooref;
  Coord euler[3];
  Coord origin[3];
  Coord pixel;
  EMparam emparam;
} TomotiltParam;

typedef struct {
  uint32_t number;
  uint32_t fileindex;
  int64_t fileoffset;
  Coord pixel;
  Coord loc[2];
  Coord defocus;
  Coord ca;
  Coord phia;
  Coord ampcon;
} TomotiltImage;

typedef struct {
  uint32_t axisindex;
  uint32_t orientindex;
  Coord origin[2];
  Coord theta;
  Coord alpha;
  Coord beta;
  Coord corr[2];
  Coord scale;
} TomotiltGeom;

typedef struct {
  uint32_t cooref;
  uint32_t reserved;
  Coord phi;
  Coord theta;
  Coord offset;
} TomotiltAxis;

typedef struct {
  uint32_t axisindex;
  uint32_t reserved;
  Coord euler[3];
} TomotiltOrient;

typedef struct {
  Size nameindex;
  Size dim;
} TomotiltFile;

typedef struct {
  TomotiltParam param;
  TomotiltImage *tiltimage;
  TomotiltGeom *tiltgeom;
  TomotiltAxis *tiltaxis;
  TomotiltOrient *tiltorient;
  TomotiltFile *tiltfile;
  char *tiltstrings;
  Size images;
  Size axes;
  Size orients;
  Size files;
  Size strings;
} Tomotilt;


/* macros */

#define TomotiltImageMax   UINT32_MAX
#define TomotiltFileMax    UINT32_MAX
#define TomotiltValMax     (9e19)


/* variables */

#ifdef TOMOTILTDEBUG

extern Size TomotiltLexDebug;
extern Size TomotiltParseDebug;

#endif


/* prototypes */

extern Tomotilt *TomotiltCreate
                 (const char *ident,
                  Size images,
                  Size axes,
                  Size orients,
                  Size files,
                  const EMparam *emparam);

extern Status TomotiltDestroy
              (Tomotilt *tomotilt);

extern Tomotilt *TomotiltRead
                 (const char *path);

extern Status TomotiltWrite
              (const Tomotilt *tomotilt,
               FILE *stream);

extern Tomotilt *TomotiltDup
                 (const Tomotilt *tomotilt);

extern Status TomotiltMat
              (const Coord euler[3],
               const TomotiltAxis *axis,
               const TomotiltOrient *orient,
               const TomotiltGeom *geom,
               Coord A0[3][3],
               Coord A[3][3],
               Coord Am[3][3],
               Coord Af[2][2],
               Bool usecorr);

extern Status TomotiltMatAxis
              (const Coord euler[3],
               const TomotiltAxis *axis,
               const TomotiltOrient *orient,
               Coord A0[3][3],
               Coord A[3][3]);

extern Status TomotiltMatAxis2
              (const TomotiltAxis *axis,
               const TomotiltGeom *geom,
               Coord Ap[2][2]);

extern Status TomotiltMatOrient
              (const Coord euler[3],
               Coord A[3][3]);

extern uint32_t TomotiltGetIndex
                (const Tomotilt *tomotilt,
                 Size number);

extern void TomotiltSetCooref
            (Tomotilt *tomotilt);

extern void TomotiltSortAngle
            (Tomotilt *tomotilt);

extern void TomotiltSortNumber
            (Tomotilt *tomotilt);


#endif
