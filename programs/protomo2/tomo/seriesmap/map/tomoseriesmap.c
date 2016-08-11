/*----------------------------------------------------------------------------*
*
*  tomoseriesmap.c  -  series: maps
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseriesmapcommon.h"
#include "exception.h"
#include "baselib.h"
#include "message.h"
#include <stdlib.h>


/* variables */

static Bool TomoseriesExtractFullimage = True;


/* functions */

extern Tomomap *TomoseriesmapCreate
                (const Tomoseries *series,
                 const TomoseriesmapParam *param)

{
  Size ori[2]; Index low[2];
  Status status;

  if ( ( param->sampling > 0 ) && ( param->sampling != series->sampling ) ) {
    pushexception( E_ARGVAL ); return NULL;
  }

  TomoseriesmapParam serparam = *param;
  serparam.flags |= series->flags & TomoLog;

  Tomoseries ser = *series;
  if ( ~serparam.flags & TomoMsg ) ser.flags &= ~TomoLog;

  TomomapParam mapparam = TomomapParamInitializer;

  mapparam.prfx = TomoseriesOutName( series, "_bck" );
  status = testcondition( mapparam.prfx == NULL );
  if ( status ) return NULL;

  mapparam.count = series->tilt->images;
  mapparam.sampling = param->sampling ? param->sampling : series->sampling;
  mapparam.mode = param->mode;
  mapparam.diam[0] = param->diam[0];
  mapparam.diam[1] = param->diam[1];
  mapparam.apod[0] = param->apod[0];
  mapparam.apod[1] = param->apod[1];
  mapparam.flags = serparam.flags;

  Tomomap *map = TomomapCreate( &mapparam );
  status = testcondition( map == NULL );
  if ( status ) goto error1;

  uint8_t *selected = malloc( series->tilt->images * sizeof(*selected) );
  if ( selected == NULL ) { status = pushexception( E_MALLOC ); goto error2; }
  TomomapSetSelected( map, selected );

  Tomoproj *proj = TomomapGetProj( map );
  TomotiltImage *tilt = series->tilt->tiltimage;
  TomodataDscr *dscr = series->data->dscr;

  if ( serparam.flags & TomoLog ) {
    Message( "extracting projections...", "\n" );
  }

  Window win = WindowInitializer;
  win.len = TomoseriesExtractFullimage ? NULL : param->len;
  win.area = param->area;

  Size count = 0;

  for ( Size index = 0; index < series->tilt->images; index++, tilt++, dscr++ ) {

    selected[index] = SelectExclude( series->selection, series->exclusion, tilt->number )
                   && SelectExclude( param->selection,  param->exclusion,  tilt->number );

    if ( selected[index] ) {

      status = TomoseriesExtract( &ser, &win, index, proj->A, proj->b, proj->len, ori, low, &proj->img );
      if ( exception( status ) ) goto error2;
      proj->b[0] -= ori[0]; proj->b[1] -= ori[1];

      proj++;
      count++;

    }

  }

  TomomapSetCount( map, count );

  ser.flags &= ~TomoLog;
  ser.flags |= mapparam.flags & TomoLog;

  TomomapMode mode = TomomapGetMode( map );
  switch ( mode.type ) {
    case TomomapBck:
    case TomomapBpr: status = TomoseriesmapInitBck( map, &ser ); break;
    default: status = pushexception( E_TOMOMAP_TYPE );
  }
  if ( status ) goto error2;

  TomomapParamFinal( &mapparam );

  return map;

  error2: TomomapDestroy( map );
  error1: TomomapParamFinal( &mapparam );

  return NULL;

}
