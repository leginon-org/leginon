/*----------------------------------------------------------------------------*
*
*  tomopatchparam.c  -  fourier: patch
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopatch.h"
#include "tomoparamread.h"
#include "maskparam.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status TomopatchGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomopatchParam *patchparam)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Status status, retstat = E_NONE;

  *patchparam = TomopatchParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, True );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  TomopatchParam patch = TomopatchParamInitializer;

  MaskParam mask = MaskParamInitializer;
  Size dim = 2;

  param = "extend";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      patch.extend = boolval;
    }
  }

  param = "complex";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      patch.complx = boolval;
    }
  }

  param = "size";
  status = TomoparamReadArraySize( tomoparam, param, patch.len, 2, NULL );
  if ( status ) {
    retstat = TomoparamReadError( sect, param, status );
  } else {
    if ( ( patch.len[0] < 4 ) || ( patch.len[1] < 4 ) ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
    patch.inc[0] = patch.len[0] / 2;
    patch.inc[1] = patch.len[1] / 2;
  }

  param = "increment";
  status = TomoparamReadArraySize( tomoparam, param, patch.inc, 2, NULL );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( !patch.inc[0] || !patch.len[1] ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  param = "area";
  status = TomoparamReadScalarCoord( tomoparam, param, &patch.area );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( patch.area > 1 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  status = TomoparamMask( tomoparam, "mask", &dim, &mask, TomoparamMaskNormal );
  if ( exception( status ) ) retstat = status;

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) goto error1;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error1;
  }

  if ( mask.flags & MaskFunctionMask ) {
    MaskParam *ptr = MaskParamNew( &patch.msk );
    if ( ptr == NULL ) { status = exception( E_MALLOC ); goto error2; }
    *ptr = mask;
  }

  *patchparam = patch;

  return E_NONE;

  error2: if ( patch.msk != NULL ) free( patch.msk );
  error1: TomoparamMaskFinal( &mask );
  return status;

}


extern Status TomopatchParamFinal
              (TomopatchParam *patchparam)

{

  if ( patchparam != NULL ) {

    TomoparamMaskParamFinal( patchparam->msk );

    if ( patchparam->msk != NULL ) free( patchparam->msk );

  }

  return E_NONE;

}
