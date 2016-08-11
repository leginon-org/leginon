/*----------------------------------------------------------------------------*
*
*  convol.h  -  array: convolution type operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef convol_h_
#define convol_h_

#include "array.h"

#define ConvolName   "convol"
#define ConvolVers   ARRAYVERS"."ARRAYBUILD
#define ConvolCopy   ARRAYCOPY


/* exception codes */

enum {
  E_CONVOL=ConvolModuleCode,
  E_CONVOL_SIZE,
  E_CONVOL_TYPE,
  E_CONVOL_MAXCODE
};


/* prototypes */

extern Status Convol2d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status Convol3d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian2d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMedian3d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean2d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMean3d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax2d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax3d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin2d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin3d
              (Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);


extern Status Convol2dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian2dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean2dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax2dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin2dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol3dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian3dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean3dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax3dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin3dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol2dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian2dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean2dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax2dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin2dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol3dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian3dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean3dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax3dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin3dUint16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol2dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian2dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean2dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax2dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin2dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol3dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian3dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean3dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax3dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin3dUint32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol2dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian2dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean2dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax2dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin2dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol3dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian3dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean3dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax3dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin3dInt8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol2dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian2dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean2dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax2dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin2dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol3dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian3dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean3dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax3dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin3dInt16
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol2dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian2dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean2dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax2dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin2dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol3dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian3dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean3dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax3dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin3dInt32
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol2dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian2dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean2dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax2dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin2dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status Convol3dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               const Real *krnaddr,
               void *dstaddr);

extern Status FilterMedian3dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *krnaddr,
               void *dstaddr);

extern Status FilterMean3dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMax3dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);

extern Status FilterMin3dReal
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr);


#endif
