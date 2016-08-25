/*----------------------------------------------------------------------------*
*
*  statistics.h  -  array: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef statistics_h_
#define statistics_h_

#include "arraydefs.h"

#define StatisticsName   "statistics"
#define StatisticsVers   ARRAYVERS"."ARRAYBUILD
#define StatisticsCopy   ARRAYCOPY


/* exception codes */

enum {
  E_STATISTICS = StatisticsModuleCode,
  E_STATISTICS_DATATYPE,
  E_STATISTICS_MAXCODE
};


/* types */

typedef enum {
  StatMin   = 0x001,
  StatMax   = 0x002,
  StatMean  = 0x004,
  StatSd    = 0x008,
  StatAll   = 0x00f,
  StatReal  = 0x000,
  StatImag  = 0x010,
  StatModul = 0x020,
  StatNoNrm = 0x100,
} StatFlags;

typedef struct {
  StatFlags flags;
} StatParam;

typedef struct {
  Size count;
  Coord min;
  Coord max;
  Coord mean;
  Coord sd;
} Stat;


/* constants */

#define StatParamInitializer  (StatParam){ 0 }

#define StatInitializer  (Stat){ 0, 0, 0, 0, 0 }


/* prototypes */

extern Status MinmaxmeanUint8
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status MinmaxmeanUint16
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status MinmaxmeanUint32
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status MinmaxmeanInt8
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status MinmaxmeanInt16
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status MinmaxmeanInt32
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status MinmaxmeanReal
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status MinmaxmeanImag
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status MinmaxmeanCmplx
              (Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status Minmaxmean
              (Type type,
               Size count,
               const void *src,
               Stat *dst,
               const StatParam *param);

extern Status HistogramUint8
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramUint16
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramUint32
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramInt8
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramInt16
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramInt32
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramReal
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramImag
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status Histogram
              (Type type,
               Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramCalcUint8
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramCalcUint16
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramCalcUint32
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramCalcInt8
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramCalcInt16
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramCalcInt32
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramCalcReal
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramCalcImag
              (Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status HistogramCalc
              (Type type,
               Size count,
               const void *src,
               Coord min,
               Coord step,
               Size n,
               Size *histo,
               Size *lower,
               Size *higher);

extern Status Sumabs2Real
              (Size size,
               const void *src,
               void *dst);

extern Status Sumabs2Cmplx
              (Size size,
               const void *src,
               void *dst);

extern Status ZeromeanReal
              (Size size,
               const void *src,
               void *dst);

extern Status ZeromeanCmplx
              (Size size,
               const void *src,
               void *dst);


#endif
