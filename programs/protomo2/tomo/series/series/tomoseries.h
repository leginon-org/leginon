/*----------------------------------------------------------------------------*
*
*  tomoseries.h  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoseries_h_
#define tomoseries_h_

#include "tomoparam.h"
#include "tomogeom.h"
#include "tomometa.h"
#include "tomodata.h"
#include "statistics.h"
#include "window.h"

#define TomoseriesName   "tomoseries"
#define TomoseriesVers   TOMOSERIESVERS"."TOMOSERIESBUILD
#define TomoseriesCopy   TOMOSERIESCOPY


/* exception codes */

enum {
  E_TOMOSERIES = TomoseriesModuleCode,
  E_TOMOSERIES_SMP,
  E_TOMOSERIES_ALI,
  E_TOMOSERIES_VOL,
  E_TOMOSERIES_MAXCODE
};


/* data structures */

typedef struct {
  Tomotilt *tilt;
  Tomometa *meta;
  Tomogeom *geom;
  Tomodata *data;
  Coord sampling;
  Coord A[3][3];
  Coord b[3];
  Size *selection;
  Size *exclusion;
  const char *prfx;
  const char *outprfx;
  const char *cacheprfx;
  Tomoflags flags;
  Status fail;
  void *final;
  void *self;
} Tomoseries;

typedef struct {
  const char *prfx;
  const char *outdir;
  const char *cachedir;
  TomodataParam data;
  Coord sampling;
  const Coord *A;
  const Coord *b;
  Size *selection;
  Size *exclusion;
  Tomoflags flags;
} TomoseriesParam;


/* constants */

#define TomoseriesInitializer  (Tomoseries){ NULL, NULL, NULL, NULL, 0, TomoMat3Undef, TomoVec3Undef, NULL, NULL, NULL, NULL, NULL, 0, E_NONE, NULL, NULL }

#define TomoseriesParamInitializer  (TomoseriesParam){ NULL, NULL, NULL, TomodataParamInitializer, 0, NULL, NULL, NULL, NULL, 0 }


/* prototypes */

extern Tomoseries *TomoseriesCreate
                   (const Tomotilt *tilt,
                    const char *metapath,
                    const TomoseriesParam *param);

extern Status TomoseriesDestroy
              (Tomoseries *series);

extern Tomoseries *TomoseriesOpen
                   (const char *metapath,
                    const TomoseriesParam *param);

extern Status TomoseriesClose
              (Tomoseries *series);

extern Tomoseries *TomoseriesNew
                   (const char *tiltpath,
                    const char *metapath,
                    const TomoseriesParam *param);

extern char *TomoseriesOutName
             (const Tomoseries *series,
              const char *sffx);

extern Status TomoseriesSampling
              (Tomoseries *series,
               const TomoseriesParam *param);

extern Tomogeom *TomoseriesGetGeom
                 (const Tomoseries *series);

extern Tomotilt *TomoseriesGetTilt
                 (const char *metapath,
                  const TomoseriesParam *param);

extern Status TomoseriesGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomoseriesParam *param);

extern Status TomoseriesSetOrigin
              (Tomoseries *series,
               const Coord origin[3]);

extern Status TomoseriesSetEuler
              (Tomoseries *series,
               const Coord euler[3]);

extern Status TomoseriesParamFinal
              (TomoseriesParam *param);

extern Status TomoseriesUpdate
              (Tomoseries *series,
               Tomotilt *tilt);

extern Status TomoseriesPreproc
              (const Tomoseries *series,
               const Size index,
               Image *img,
               void **addr);

extern void TomoseriesResampleGeom
            (const TomodataDscr *dscr,
             Coord sampling,
             Coord Ap[3][2],
             Coord Bp[3][2]);

extern void TomoseriesResampleGeom3
            (const TomodataDscr *dscr,
             Coord sampling,
             Coord A[3][3],
             Coord a[2],
             Coord B[3][3],
             Coord b[2]);

extern void TomoseriesResampleTransform
            (const Tomoseries *series,
             const Size index,
             Coord Ap[3][2],
             Coord Bp[3][2]);

extern Status TomoseriesResample
              (const Tomoseries *series,
               const Window *win,
               const Size index,
               Coord Ap[3][2],
               Real *winaddr,
               Stat *winstat,
               const MaskParam *winmsk);

extern Status TomoseriesResampleArea
              (const Tomoseries *series,
               const Window *win,
               const Size index,
               Coord Ap[3][2],
               uint16_t *mskaddr);

extern Status TomoseriesExtract
              (const Tomoseries *series,
               const Window *win,
               const Size index,
               Coord B[3][3],
               Coord b[2],
               Size dstlen[2],
               Size dstori[2],
               Index dstlow[2],
               Real **dstaddr);

extern Status TomoseriesExtractWrite
              (const Tomoseries *series,
               const Window *win,
               const Size nz,
               const char *path);

extern Status TomoseriesWindow
              (const Tomoseries *series,
               const Window *win,
               Image *img,
               Real **addr,
               Bool aligned);

extern Status TomoseriesWindowImage
              (const Tomoseries *series,
               const Window *win,
               const Size index,
               Image *img,
               void **addr,
               Bool aligned);

extern Status TomoseriesWindowWrite
              (const Tomoseries *series,
               const Window *win,
               const char *path,
               Bool aligned);

extern Status TomoseriesArea
              (const Tomoseries *series,
               const Window *win,
               Image *img,
               uint16_t **addr,
               Bool aligned);

extern Status TomoseriesAreaWrite
              (const Tomoseries *series,
               const Window *win,
               const char *path,
               Bool aligned);

extern Status TomoseriesVolume
              (const Tomoseries *series,
               const Size nz,
               Image *img,
               uint16_t **addr,
               Size len[2],
               Index low[2]);

extern Status TomoseriesVolumeWrite
              (const Tomoseries *series,
               const Size nz,
               const char *path);


#endif
