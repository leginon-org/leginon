/*----------------------------------------------------------------------------*
*
*  tomomap.h  -  map: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomomap_h_
#define tomomap_h_

#include "tomomapdefs.h"
#include "tomotransfer.h"
#include "tomoparamread.h"
#include "i3data.h"

#define TomomapName   "tomomap"
#define TomomapVers   TOMOMAPVERS"."TOMOMAPBUILD
#define TomomapCopy   TOMOMAPCOPY


/* exception codes */

enum {
  E_TOMOMAP = TomomapModuleCode,
  E_TOMOMAP_SAMP,
  E_TOMOMAP_TYPE,
  E_TOMOMAP_MAXCODE
};


/* data structures */

typedef enum {
  TomomapUndef,
  TomomapBck,
  TomomapBpr,
} TomomapType;

typedef struct {
  TomomapType type;
  union {
    struct {
      Coord body;
      Coord bwid;
      Coord bthr;
    } bck;
  } param;
} TomomapMode;

typedef struct {
  Size len[2];
  Real *img;
  Coord A[3][3];
  Coord b[2];
} Tomoproj;

struct _Tomomap;

typedef struct _Tomomap Tomomap;

struct _Tomocomp;

typedef struct _Tomocomp Tomocomp;

typedef struct {
  const char *prfx;
  Size count;
  Coord sampling;
  TomomapMode mode;
  Coord diam[2];
  Coord apod[2];
  Tomoflags flags;
} TomomapParam;


/* constants */

#define TomomapModeInitializer  (TomomapMode){ TomomapUndef, { { 0, 0, 0 } } }

#define TomomapParamInitializer  (TomomapParam){ NULL, 0, 0, TomomapModeInitializer, { 0, 0 }, { 0, 0 }, 0 }


/* prototypes */

extern Tomomap *TomomapCreate
                (const TomomapParam *param);

extern Status TomomapDestroy
              (Tomomap *map);

extern Tomoproj *TomomapGetProj
                 (Tomomap *map);

extern TomomapMode TomomapGetMode
                   (Tomomap *map);

extern uint8_t *TomomapGetSelected
                (Tomomap *map);

extern const I3data *TomocompGetExtra
                     (Tomocomp *comp);

extern void TomomapSetCount
            (Tomomap *map,
             Size count);

extern void TomomapSetSelected
            (Tomomap *map,
             uint8_t *selected);

extern Tomocomp *TomocompBeginMem
                 (Tomomap *map,
                  const Size len[3]);

extern Real *TomocompEndMem
             (Tomocomp *comp,
              Status fail);

extern Tomocomp *TomocompBeginFile
                 (const char *path,
                  const char *fmt,
                  Tomomap *map,
                  const Size len[3]);

extern Status TomocompEndFile
              (Tomocomp *comp,
               Status fail);

extern Status TomomapOut
              (const char *prfx,
               const char *sffx,
               const Size number,
               const Size dim,
               const Size *len,
               const Index *low,
               const Type type,
               const ImageAttr attr,
               const void *addr);

extern Status TomomapGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomomapParam *mapparam);

extern Status TomomapParamFinal
              (TomomapParam *mapparam);


#endif
