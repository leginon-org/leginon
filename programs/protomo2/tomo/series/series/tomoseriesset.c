/*----------------------------------------------------------------------------*
*
*  tomoseriesset.c  -  series: tomography
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
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomoseriesSetSampling
              (const TomoseriesParam *param,
               const char *cacheprfx,
               TomodataParam *datapar,
               Tomoflags *flags,
               Coord *sampling)

{

  if ( ( param->sampling < 1 ) && ( param->sampling != 0 ) ) {
    return pushexception( E_TOMOSERIES_SMP );
  }

  *sampling = ( param->sampling > 1 ) ? param->sampling : 1;
  *flags = param->flags & TomoflagMask;

  *datapar = param->data;
  datapar->cacheprfx = cacheprfx;
  datapar->flags = *flags;
  datapar->sampling = *sampling;
  if ( ( datapar->sampling < 2 ) || !( *flags & TomoSmp ) ) {
    datapar->sampling = 1;
    *flags &= ~TomoSmp;
  }

  return E_NONE;

}


static Status TomoseriesCreateSelect
              (const Size *select,
               Size **seladdr)

{
  Size *addr = NULL;
  Status status = E_NONE;

  if ( select != NULL ) {

    Size len = ( 2 * *select + 1 ) * sizeof(*select);
    addr = malloc( len );
    if ( addr == NULL ) {
      status = exception( E_MALLOC );
    } else {
      memcpy( addr, select, len );
    }

  }

  *seladdr = addr;

  return status;

}


static Status TomoseriesSetSelect
              (const TomoseriesParam *param,
               Tomoseries *series)

{
  Status status;

  if ( series->selection != NULL ) {
    free( series->selection ); series->selection = NULL;
  }

  if ( series->exclusion != NULL ) {
    free( series->exclusion ); series->exclusion = NULL;
  }

  status = TomoseriesCreateSelect( param->selection, &series->selection );
  if ( exception( status ) ) return status;

  status = TomoseriesCreateSelect( param->exclusion, &series->exclusion );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status TomoseriesSetParam
              (const TomoseriesParam *param,
               const char *cacheprfx,
               TomodataParam *datapar,
               Tomoseries *series)

{
  Status status;

  status = TomoseriesSetSampling( param, cacheprfx, datapar, &series->flags, &series->sampling );
  if ( exception( status ) ) return status;

  status = TomoseriesSetSelect( param, series );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status TomoseriesSetOrigin
              (Tomoseries *series,
               const Coord origin[3])

{
  Status status;

  status = TomometaSetOrigin( series->meta, series->tilt, origin );
  if ( exception( status ) ) return status;

  status = TomogeomInit( series->tilt, series->A, series->b, series->geom );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status TomoseriesSetEuler
              (Tomoseries *series,
               const Coord euler[3])

{
  Status status;

  status = TomometaSetEuler( series->meta, series->tilt, euler );
  if ( exception( status ) ) return status;

  status = TomogeomInit( series->tilt, series->A, series->b, series->geom );
  if ( exception( status ) ) return status;

  return E_NONE;

}
