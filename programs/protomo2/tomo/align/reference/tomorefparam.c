/*----------------------------------------------------------------------------*
*
*  tomorefparam.c  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomorefcommon.h"
#include "tomoparamread.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status TomorefGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomorefParam *refparam)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Status status, retstat = E_NONE;

  *refparam = TomorefParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) {
      refparam->mode.type = TomorefSeq;
      return E_NONE;
    }
  }

  TomorefParam ref = TomorefParamInitializer;
  TomotransferParam transfer = TomotransferParamInitializer;
  ref.mode.type = TomorefSeq;
  const char *mpar = NULL;

  param = "logging";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      ref.flags |= TomoLog;
    }
  }

  param = "select";
  status = TomoparamReadSelection( tomoparam, param, &ref.selection );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "exclude";
  status = TomoparamReadSelection( tomoparam, param, &ref.exclusion );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "dz";
  status = TomoparamReadScalarCoord( tomoparam, param, &ref.mode.param.mrg.dz );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ref.mode.param.mrg.dz <= 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      ref.mode.type = TomorefMrg;
      mpar = param;
    }
  }

  status = TomotransferGetParam( tomoparam, NULL, &transfer );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = status;
    } else if ( mpar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, "body", mpar );
    } else {
      ref.mode.type = ( transfer.bfsh == 0 ) ? TomorefBck : TomorefBpr;
      ref.mode.param.bck.body = transfer.body;
      ref.mode.param.bck.bwid = transfer.bwid;
      ref.mode.param.bck.bthr = transfer.bthr;
      mpar = param;
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) goto error;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error;
  }

  *refparam = ref;

  return E_NONE;

  error: if ( ref.selection != NULL ) free( ref.selection );
         if ( ref.exclusion != NULL ) free( ref.exclusion );
  return status;

}


extern Status TomorefParamFinal
              (TomorefParam *refparam)

{

  if ( refparam != NULL ) {

    if ( refparam->selection != NULL ) free( refparam->selection );
    if ( refparam->exclusion != NULL ) free( refparam->exclusion );

  }

  return E_NONE;

}
