/*----------------------------------------------------------------------------*
*
*  mask.h  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef mask_h_
#define mask_h_

#include "array.h"
#include "statistics.h"

#define MaskName   "mask"
#define MaskVers   ARRAYVERS"."ARRAYBUILD
#define MaskCopy   ARRAYCOPY


/* exception codes */

enum {
  E_MASK = MaskModuleCode,
  E_MASK_DIM,
  E_MASK_TYPE,
  E_MASK_MODE,
  E_MASK_FUNC,
  E_MASK_MAXCODE
};


/* types */

typedef enum {
   /* mask functions */
  MaskFunctionNone   = 0x00,
  MaskFunctionRect   = 0x01,
  MaskFunctionEllips = 0x02,
  MaskFunctionGauss  = 0x03,
  MaskFunctionWedge  = 0x04,
  MaskFunctionMask   = 0x0f,
  /* mask modes */
  MaskModeNormal = 0x0000,
  MaskModeInv    = 0x0100,
  MaskModeApod   = 0x0200,
  MaskModeAuto   = 0x0400,
  MaskModeVal    = 0x0800,
  MaskModeFract  = 0x1000,
  MaskModeUnit   = 0x2000,
  MaskModeNodd   = 0x4000,
  MaskModeSym    = 0x8000,
  MaskModeMask   = 0xff00,
} MaskFlags;

typedef struct {
  Coord *A;
  Coord *b;
  Coord *wid;
  Coord *apo;
  Coord val;
  MaskFlags flags;
} MaskParam;


/* constants */

#define MaskParamInitializer  (MaskParam){ NULL, NULL, NULL, NULL, 0, MaskFunctionNone }


/* prototypes */

extern Status Mask
              (Size dim,
               const Size *len,
               Type type,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskRect
              (Size dim,
               const Size *len,
               Type type,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskEllips
              (Size dim,
               const Size *len,
               Type type,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskGauss
              (Size dim,
               const Size *len,
               Type type,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskWedge
              (Size dim,
               const Size *len,
               Type type,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskReal
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskRectReal
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskEllipsReal
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskGaussReal
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskWedgeReal
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskCmplx
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskRectCmplx
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskEllipsCmplx
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskGaussCmplx
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskWedgeCmplx
              (Size dim,
               const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const MaskParam *param);

extern Status MaskRect2dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Real v,
               MaskFlags flags);

extern Status MaskRect2dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags);

extern Status MaskRect3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Real v,
               MaskFlags flags);

extern Status MaskRect3dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags);

extern Status MaskRectApod2dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Real v,
               MaskFlags flags);

extern Status MaskRectApod2dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Cmplx v,
               MaskFlags flags);

extern Status MaskRectApod3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Real v,
               MaskFlags flags);

extern Status MaskRectApod3dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Cmplx v,
               MaskFlags flags);

extern Status MaskEllips2dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Real v,
               MaskFlags flags);

extern Status MaskEllips2dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags);

extern Status MaskEllips3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Real v,
               MaskFlags flags);

extern Status MaskEllips3dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags);

extern Status MaskEllipsApod2dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Real v,
               MaskFlags flags);

extern Status MaskEllipsApod2dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Cmplx v,
               MaskFlags flags);

extern Status MaskEllipsApod3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Real v,
               MaskFlags flags);

extern Status MaskEllipsApod3dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               const Coord *s,
               Cmplx v,
               MaskFlags flags);

extern Status MaskGauss2dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Real v,
               MaskFlags flags);

extern Status MaskGauss2dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags);

extern Status MaskGauss3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Real v,
               MaskFlags flags);

extern Status MaskGauss3dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags);

extern Status MaskWedge3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Real v,
               MaskFlags flags);

extern Status MaskWedge3dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags);

extern Status MaskWedgeApod3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Real v,
               MaskFlags flags);

extern Status MaskWedgeApod3dCmplx
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Cmplx v,
               MaskFlags flags);

extern Status MaskStatRect2dReal
              (const Size *len,
               const void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Stat *dst,
               MaskFlags flags);

extern Status MaskStatRect3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Stat *dst,
               MaskFlags flags);

extern Status MaskStatEllips2dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Stat *dst,
               MaskFlags flags);

extern Status MaskStatEllips3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Stat *dst,
               MaskFlags flags);

extern Status MaskStatWedge3dReal
              (const Size *len,
               void *addr,
               const Coord *A,
               const Coord *b,
               const Coord *w,
               Stat *dst,
               MaskFlags flags);


#endif
