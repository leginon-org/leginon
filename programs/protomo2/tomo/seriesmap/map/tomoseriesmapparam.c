/*----------------------------------------------------------------------------*
*
*  tomoseriesmapparam.c  -  series: maps
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseriesmap.h"
#include "tomoparamread.h"
#include "strings.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status TomoseriesmapGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               const TomoseriesParam *seriesparam,
               TomoseriesmapParam *mapparam)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Status status, retstat = E_NONE;

  *mapparam = TomoseriesmapParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, True );
    if ( exception( status ) ) return status;
  }

  TomoseriesmapParam map = TomoseriesmapParamInitializer;

  param = "size";
  status = TomoparamReadArraySize( tomoparam, param, map.len, 3, NULL );
  if ( status ) {
    retstat = TomoparamReadError( sect, param, status );
  } else {
    for ( Size i = 0; i < 3; i++ ) {
      if ( !map.len[i] ) {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      }
    }
  }

  param = "binning";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      map.flags |= TomoSmp;
    }
  } else if ( seriesparam != NULL ) {
    map.flags |= seriesparam->flags & TomoSmp;
  }

  param = "sampling";
  status = TomoparamReadScalarCoord( tomoparam, param, &map.sampling );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( map.sampling < 1 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  } else if ( seriesparam != NULL ) {
    map.sampling = seriesparam->sampling;
  }

  param = "area";
  status = TomoparamReadScalarCoord( tomoparam, param, &map.area );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( map.area > 1 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  param = "select";
  status = TomoparamReadSelection( tomoparam, param, &map.selection );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "exclude";
  status = TomoparamReadSelection( tomoparam, param, &map.exclusion );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  TomomapParam mappar = TomomapParamInitializer;
  status = TomomapGetParam( tomoparam, NULL, &mappar );
  if ( exception( status ) ) retstat = status;
  map.mode = mappar.mode;
  map.diam[0] = mappar.diam[0];
  map.diam[1] = mappar.diam[1];
  map.apod[0] = mappar.apod[0];
  map.apod[1] = mappar.apod[1];
  map.flags |= mappar.flags;
  TomomapParamFinal( &mappar );

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) goto error;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error;
  }

  *mapparam = map;

  return E_NONE;

  error: if ( map.selection != NULL ) free( map.selection );
         if ( map.exclusion != NULL ) free( map.exclusion );

  return status;

}


extern Status TomoseriesmapParamFinal
              (TomoseriesmapParam *mapparam)

{

  if ( mapparam != NULL ) {

    if ( mapparam->selection != NULL ) free( mapparam->selection );
    if ( mapparam->exclusion != NULL ) free( mapparam->exclusion );

  }

  return E_NONE;

}
