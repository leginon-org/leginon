/*----------------------------------------------------------------------------*
*
*  imagestat.c  -  image: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagestat.h"
#include "imagearray.h"
#include "exception.h"
#include "signals.h"
#include "mathdefs.h"


/* types */

typedef struct {
  Stat stat;
  StatParam param;
} ImageStatData;


/* functions */

static Status StatExec
              (Type type,
               Size srclen,
               const void *srcpos,
               const void *srcneg,
               Size dstlen,
               void *dst)

{
  ImageStatData *data = dst;
  Stat stat = StatInitializer;
  Status status;

  if ( SignalInterrupt ) return exception( E_SIGNAL );

  status = Minmaxmean( type, srclen, srcpos, &stat, &data->param );
  if ( exception( status ) ) return status;

  data->stat.count += stat.count;
  if ( stat.min < data->stat.min ) data->stat.min = stat.min;
  if ( stat.max > data->stat.max ) data->stat.max = stat.max;
  data->stat.mean += stat.mean;
  data->stat.sd += stat.sd;

  return E_NONE;

}


extern Status ImageStat
              (const Image *src,
               const void *srcaddr,
               Stat *dst,
               const ImageStatParam *param)

{
  static const ImageFnTab fntab = {
    StatExec,
    StatExec,
    StatExec,
    StatExec,
    StatExec,
  };
  ImageStatData data;
  Status status;

  if ( src  == NULL ) return exception( E_ARGVAL );
  if ( srcaddr == NULL ) return exception( E_ARGVAL );

  data.stat = StatInitializer;

  data.stat.min = +CoordMax;
  data.stat.max = -CoordMax;

  data.param = StatParamInitializer;

  data.param.flags = ( param == NULL ) ? StatAll : param->stat.flags & StatAll;

  if ( TypeIsCmplx( src->type ) ) data.param.flags |= StatModul;

  data.param.flags |= StatNoNrm;

  status = ImageFnsExec( &fntab, src, srcaddr, &data );
  if ( exception( status ) ) return status;

  if ( dst != NULL ) {
    *dst = data.stat;
    if ( data.stat.count ) {
      dst->mean /= data.stat.count;
      dst->sd = Sqrt( dst->sd / data.stat.count );
    }
  }

  return E_NONE;

}
