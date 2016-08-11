/*----------------------------------------------------------------------------*
*
*  tomoparamtransfer.c  -  core: retrieve parameters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoparamreadcommon.h"
#include "exception.h"


/* functions */

extern Status TomoparamTransfer
              (Tomoparam *tomoparam,
               const char *ident,
               TransferParam *transferparam)

{
  const char *sect;
  const char *param;
  Coord val[2], out[2];
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( transferparam == NULL ) ) return pushexception( E_ARGVAL );

  *transferparam = TransferParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  TransferParam transfer = TransferParamInitializer;
  const char *bpar = NULL;
  const char *spar = NULL;
  const char *ipar = NULL;

  param = "thr";
  status = TomoparamReadArrayCoord( tomoparam, param, val, 2, NULL );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      transfer.thrmin = val[0];
      transfer.thrmax = val[1];
      transfer.flags |= TransferThr;
    }
  }

  param = "bias";
  status = TomoparamReadScalarCoord( tomoparam, param, &transfer.bias );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      transfer.flags |= TransferBias;
      bpar = param;
    }
  }

  param = "scale";
  status = TomoparamReadScalarCoord( tomoparam, param, &transfer.scale );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      transfer.flags |= TransferScale;
      spar = param;
    }
  }

  param = "in"; ipar = param;
  status = TomoparamReadArrayCoord( tomoparam, param, val, 2, NULL );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ( bpar != NULL ) || ( spar != NULL ) ) {
      if ( bpar != NULL ) retstat = TomoparamReadErrorConflict( sect, param, bpar );
      if ( spar != NULL ) retstat = TomoparamReadErrorConflict( sect, param, spar );
    }
    ipar = NULL;
  }

  param = "out";
  status = TomoparamReadArrayCoord( tomoparam, param, out, 2, NULL );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ( bpar != NULL ) || ( spar != NULL ) ) {
      if ( bpar != NULL ) retstat = TomoparamReadErrorConflict( sect, param, bpar );
      if ( spar != NULL ) retstat = TomoparamReadErrorConflict( sect, param, spar );
    } else if ( ipar != NULL ) {
      retstat = TomoparamReadError( sect, ipar, E_TOMOPARAM_UNDEF );
    } else {
      Coord range = val[1] - val[0];
      if ( range != 0 ) {
        transfer.scale = ( out[1] - out[0] ) / range;
        if ( transfer.scale != 0 ) {
          transfer.bias = ( val[0] + val[1] - ( out[0] + out[1] ) / transfer.scale ) / 2;
        }
      }
      transfer.flags |= TransferScale | TransferBias;
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat ) {
    *transferparam = transfer;
  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

}
