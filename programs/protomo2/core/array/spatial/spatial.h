/*----------------------------------------------------------------------------*
*
*  spatial.h  -  array: spatial operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef spatial_h_
#define spatial_h_

#include "array.h"

#define SpatialName   "spatial"
#define SpatialVers   ARRAYVERS"."ARRAYBUILD
#define SpatialCopy   ARRAYCOPY


/* exception codes */

enum {
  E_SPATIAL=SpatialModuleCode,
  E_SPATIAL_PEAK,
  E_SPATIAL_MAXCODE
};


/* types */

typedef enum {
  PeakOriginCentered = 0x01,
  PeakOriginRelative = 0x02,
  PeakModeCyc        = 0x04,
  PeakCMEllips       = 0x10,
  PeakHeightInterp   = 0x20,
  PeakParamDefined   = 0x100
} PeakFlags;

typedef struct {
  Coord *ctr;
  Coord *rad;
  Coord *cmrad;
  PeakFlags flags;
} PeakParam;


/* constants */

#define PeakParamInitializer (PeakParam){ NULL, NULL, NULL, 0 }


/* prototypes */

extern Status PeakReal
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               Size *ipos,
               Coord *pos,
               void *pk,
               const PeakParam *param);

extern Status Peak1dReal
              (const Size *srclen,
               const void *srcaddr,
               Size *ipos,
               Coord *pos,
               void *pk,
               const PeakParam *param);

extern Status Peak2dReal
              (const Size *srclen,
               const void *srcaddr,
               Size *ipos,
               Coord *pos,
               void *pk,
               const PeakParam *param);

extern Status Peak3dReal
              (const Size *srclen,
               const void *srcaddr,
               Size *ipos,
               Coord *pos,
               void *pk,
               const PeakParam *param);

extern Status GradientLin1dReal
              (const Size *srclen,
               const void *srcaddr,
               Coord *c);

extern Status GradientLin2dReal
              (const Size *srclen,
               const void *srcaddr,
               Coord *c);

extern Status GradientLin3dReal
              (const Size *srclen,
               const void *srcaddr,
               Coord *c);

extern Status GradcorrLin1dReal
              (const Size *dstlen,
               void *dstaddr,
               const Coord *c);

extern Status GradcorrLin2dReal
              (const Size *dstlen,
               void *dstaddr,
               const Coord *c);

extern Status GradcorrLin3dReal
              (const Size *dstlen,
               void *dstaddr,
               const Coord *c);


#endif
