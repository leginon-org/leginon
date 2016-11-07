/*----------------------------------------------------------------------------*
*
*  tomoseriessampling.c  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseriesset.h"
#include "exception.h"


/* functions */

extern Status TomoseriesSampling
              (Tomoseries *series,
               const TomoseriesParam *param)

{
  TomodataParam datapar;
  Tomoflags flags;
  Coord sampling;
  Status status;

  status = TomoseriesSetSampling( param, series->cacheprfx, &datapar, &flags, &sampling );
  if ( exception( status ) ) return status;

  Tomodata *data = series->data;

  if ( ( data->sampling != datapar.sampling ) || ( ( series->flags ^ flags ) & ( TomoPreproc | TomoSmp ) ) ) {

    Tomocache *cache = data->cache;
    if ( cache != NULL ) {
      data->cache = NULL;
      data->flags &= ~TomoflagInit;
      status = TomocacheDestroy( cache, E_NONE );
      if ( exception( status ) ) return status;
    }

    status = TomodataInit( series->data, &datapar );
    if ( exception( status ) ) return status;

  }

  series->sampling = sampling;
  series->flags = flags;

  return E_NONE;

}
