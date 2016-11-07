/*----------------------------------------------------------------------------*
*
*  tomoref.h  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoref_h_
#define tomoref_h_

#include "tomoimage.h"
#include "tomotransfer.h"
#include "windowfourier.h"

#define TomorefName   "tomoref"
#define TomorefVers   TOMOALIGNVERS"." TOMOALIGNBUILD
#define TomorefCopy   TOMOALIGNCOPY


/* exception codes */

enum {
  E_TOMOREF = TomorefModuleCode,
  E_TOMOREF_TYPE,
  E_TOMOREF_ZERO,
  E_TOMOREF_MAXCODE
};


/* types */

typedef enum {
  TomorefUndef,
  TomorefSeq,
  TomorefMrg,
  TomorefBck,
  TomorefBpr,
  TomorefMax
} TomorefType;

typedef struct {
  TomorefType type;
  union {
    struct {
      Coord dz;
    } mrg;
    struct {
      Coord body;
      Coord bwid;
      Coord bthr;
    } bck;
  } param;
} TomorefMode;

typedef struct {
  Cmplx *transform;
  Real *transfer;
} TomorefImage;

typedef struct {
  const Tomoseries *series;
  const Tomoimage *image;
  const Window *window;
  const WindowFourier *fourier;
  TomorefMode mode;
  TomorefImage *refimage;
  Tomotransfer *trans;
  Size transcount;
  Size mincount;
  Size maxcount;
  Size minref;
  Size maxref;
  Size excl;
  Tomoflags flags;
} Tomoref;

typedef struct {
  TomorefMode mode;
  Size *selection;
  Size *exclusion;
  Tomoflags flags;
} TomorefParam;


/* constants */

#define TomorefModeInitializer  (TomorefMode){ TomorefUndef, { { 0 } } }

#define TomorefInitializer  (Tomoref){ NULL, NULL, NULL, NULL, TomorefModeInitializer, NULL, NULL, 0, 0, 0, 0, 0, SizeMax, 0 }

#define TomorefParamInitializer  (TomorefParam){ TomorefModeInitializer, NULL, NULL, 0 }


/* prototypes */

extern Tomoref *TomorefCreate
                (const Tomoseries *series);

extern Status TomorefDestroy
              (Tomoref *ref);

extern Status TomorefInit
              (Tomoref *ref,
               Tomoimage *image,
               const Window *window,
               const WindowFourier *fourier,
               const TomorefParam *param);

extern Status TomorefFinal
              (Tomoref *ref);

extern Status TomorefGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomorefParam *param);

extern Status TomorefParamFinal
              (TomorefParam *param);

extern Status TomorefStart
              (Tomoref *ref,
               Size count);

extern Status TomorefNew
              (Tomoref *ref,
               Size exclindex);

extern Status TomorefUpdate
              (Tomoref *ref,
               Size mincount,
               Size maxcount);

extern Cmplx *TomorefTransform
              (const Tomoref *ref,
               const Size *refsort,
               Size refindex,
               const Size *imgsort,
               Size imgindex);



#endif
