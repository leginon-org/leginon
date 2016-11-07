/*----------------------------------------------------------------------------*
*
*  tomotransferparam.c  -  tomography: transfer functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotransfer.h"
#include "tomoparamread.h"
#include "exception.h"


/* functions */

extern Status TomotransferGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomotransferParam *transferparam)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Status status, retstat = E_NONE;

  *transferparam = TomotransferParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_TOMOPARAM_UNDEF;
  }

  TomotransferParam transfer = TomotransferParamInitializer;
  const char *tpar;

  param = "body"; tpar = param;
  status = TomoparamReadScalarCoord( tomoparam, param, &transfer.body );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( transfer.body <= 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      tpar = NULL;
    }
  }

  param = "bwid";
  status = TomoparamReadScalarCoord( tomoparam, param, &transfer.bwid );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( transfer.bwid < 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else if ( tpar != NULL ) {
      retstat = TomoparamReadError( sect, tpar, E_TOMOPARAM_UNDEF );
      tpar = NULL;
    }
  }

  param = "bthr";
  status = TomoparamReadScalarCoord( tomoparam, param, &transfer.bthr );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( transfer.bthr <= 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else if ( tpar != NULL ) {
      retstat = TomoparamReadError( sect, tpar, E_TOMOPARAM_UNDEF );
      tpar = NULL;
    }
  } else {
    transfer.bthr = 1.0;
  }

  param = "slab";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( tpar != NULL ) {
      retstat = TomoparamReadError( sect, tpar, E_TOMOPARAM_UNDEF );
      tpar = NULL;
    } else if ( boolval ) {
      transfer.bfsh = 1;
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat ) {
    *transferparam = transfer;
  }

  status = ( tpar != NULL ) ? E_TOMOPARAM_UNDEF : E_NONE;

  return retstat ? E_TOMOPARAMREAD_ERROR : status;

}
