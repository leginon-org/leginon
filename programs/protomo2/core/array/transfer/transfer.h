/*----------------------------------------------------------------------------*
*
*  transfer.h  -  array: pixel value transfer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef transfer_h_
#define transfer_h_

#include "arraydefs.h"

#define TransferName   "transfer"
#define TransferVers   ARRAYVERS"."ARRAYBUILD
#define TransferCopy   ARRAYCOPY


/* exception codes */

enum {
  E_TRANSFER = TransferModuleCode,
  E_TRANSFER_DATATYPE,
  E_TRANSFER_MAXCODE
};


/* types */

typedef enum {
  TransferThr   = 0x03,  /* threshold after scaling, min <= val <= max */
  TransferBias  = 0x04,  /* subtract bias */
  TransferScale = 0x08   /* scale after applying bias */
} TransferFlags;

typedef struct {
  Coord thrmin;
  Coord thrmax;
  Coord bias;
  Coord scale;
  TransferFlags flags;
} TransferParam;


/* constants */

#define TransferParamInitializer  (TransferParam){ 0, 0, 0, 0, 0 }


/* prototypes */

extern Status ScaleUint8Real
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleUint16Real
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleUint32Real
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleInt8Real
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleInt16Real
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleInt32Real
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleRealReal
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleReal
              (Type type,
               Size count,
               const void *src,
               void *dst,
               const TransferParam *param);


extern Status ScaleImag
              (Type type,
               Size count,
               const void *src,
               void *dst,
               const TransferParam *param);


extern Status ScaleRealCmplx
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleImagCmplx
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleCmplxCmplx
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleCmplx
              (Type type,
               Size count,
               const void *src,
               void *dst,
               const TransferParam *param);


extern Status ScaleRealUint8
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleRealUint16
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleRealUint32
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleRealInt8
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleRealInt16
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleRealInt32
              (Size count,
               const void *src,
               void *dst,
               const TransferParam *param);

extern Status ScaleType
              (Type type,
               Size count,
               const void *src,
               void *dst,
               const TransferParam *param);



#endif
