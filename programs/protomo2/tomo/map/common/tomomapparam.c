/*----------------------------------------------------------------------------*
*
*  tomomapparam.c  -  map: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomomap.h"
#include "tomoparamread.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status TomomapGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomomapParam *mapparam)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Status status, retstat = E_NONE;

  *mapparam = TomomapParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  TomomapParam map = TomomapParamInitializer;
  TomotransferParam transfer = TomotransferParamInitializer;

  param = "logging";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      map.flags |= TomoMsg;
    }
  }

  status = TomotransferGetParam( tomoparam, NULL, &transfer );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = status;
    } else {
      map.mode.type = ( transfer.bfsh == 0 ) ? TomomapBck : TomomapBpr;
      map.mode.param.bck.body = transfer.body;
      map.mode.param.bck.bwid = transfer.bwid;
      map.mode.param.bck.bthr = transfer.bthr;
    }
  }

  const char *subsect = "lowpass";

  status = TomoparamReadPush( tomoparam, subsect, &sect, False );
  if ( exception( status ) ) return status;

  if ( sect != NULL ) {

    const char *dparam = "diameter";

    param = dparam;
    status = TomoparamReadArrayCoord( tomoparam, param, map.diam, 2, NULL );
    if ( status != E_TOMOPARAM_UNDEF ) {
      if ( status ) {
        retstat = TomoparamReadError( sect, param, status );
      } else if ( ( map.diam[0] <= 0 ) || ( map.diam[1] <= 0 ) ) {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      }
      dparam = NULL;
    }

    param = "apodization";
    status = TomoparamReadArrayCoord( tomoparam, param, map.apod, 2, NULL );
    if ( status != E_TOMOPARAM_UNDEF ) {
      if ( status ) {
        retstat = TomoparamReadError( sect, param, status );
      } else if ( ( map.apod[0] <= 0 ) || ( map.apod[1] <= 0 ) ) {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      } else if ( dparam != NULL ) {
        retstat = TomoparamReadError( sect, dparam, E_TOMOPARAM_UNDEF );
      }
    } else if ( dparam == NULL ) {
      map.apod[0] = map.diam[0] / 20;
      map.apod[1] = map.diam[1] / 20;
    }

    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;

  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat ) {
    *mapparam = map;
  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

}


extern Status TomomapParamFinal
              (TomomapParam *mapparam)

{

  if ( mapparam != NULL ) {
    if ( mapparam->prfx != NULL ) free( (char *)mapparam->prfx );
    *mapparam = TomomapParamInitializer;
  }

  return E_NONE;

}
