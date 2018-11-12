/*----------------------------------------------------------------------------*
*
*  tomowindowparam.c  -  align: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomowindow.h"
#include "tomoparamread.h"
#include "maskparam.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status TomowindowGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomowindowParam *tomowindowparam)

{
  const char *sect;
  Status status, retstat = E_NONE;

  *tomowindowparam = TomowindowParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, True );
    if ( exception( status ) ) return status;
  }

  WindowParam windowparam = WindowParamInitializer;
  MaskParam mask, *msk = NULL, *flt = NULL;
  Size dim = 2; Size len[2];

  status = TomoparamWindow( tomoparam, NULL, &dim, len, &windowparam );
  if ( exception( status ) ) retstat = status;

  status = TomoparamMask( tomoparam, "mask", &dim, &mask, TomoparamMaskNormal );
  if ( exception( status ) ) retstat = status;
  if ( mask.flags & MaskFunctionMask ) {
    MaskParam *ptr = MaskParamNew( &msk );
    if ( ptr == NULL ) { retstat = pushexception( E_MALLOC ); goto exit; }
    *ptr = mask;
  }

  status = TomoparamMask( tomoparam, "lowpass", &dim, &mask, TomoparamMaskNormal | TomoparamMaskFourier );
  if ( exception( status ) ) retstat = status;
  if ( mask.flags & MaskFunctionMask ) {
    MaskParam *ptr = MaskParamNew( &flt );
    if ( ptr == NULL ) { retstat = pushexception( E_MALLOC ); goto exit; }
    *ptr = mask;
  }

  status = TomoparamMask( tomoparam, "highpass", &dim, &mask, TomoparamMaskInv | TomoparamMaskFourier );
  if ( exception( status ) ) retstat = status;
  if ( mask.flags & MaskFunctionMask ) {
    MaskParam *ptr = MaskParamNew( &flt );
    if ( ptr == NULL ) { retstat = pushexception( E_MALLOC ); goto exit; }
    *ptr = mask;
  }

  status = TomoparamMaskWedge( tomoparam, "wedge", &dim, &mask, TomoparamMaskInv | TomoparamMaskFourier );
  if ( exception( status ) ) retstat = status;
  if ( mask.flags & MaskFunctionMask ) {
    MaskParam *ptr = MaskParamNew( &flt );
    if ( ptr == NULL ) { retstat = pushexception( E_MALLOC ); goto exit; }
    *ptr = mask;
  }

  exit:

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) retstat = status;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error;
  }

  tomowindowparam->len[0] = len[0];
  tomowindowparam->len[1] = len[1];
  tomowindowparam->area = windowparam.area;
  tomowindowparam->msk = msk;
  tomowindowparam->flt = flt;

  return E_NONE;

  error:
  TomoparamWindowFinal( &windowparam );
  if ( flt != NULL ) free( flt );
  return status;

}


extern Status TomowindowCorrGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomowindowCorrParam *tomowindowcorrparam)

{
  const char *sect;
  const char *param;
  Status status, retstat = E_NONE;

  *tomowindowcorrparam = TomowindowCorrParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, True );
    if ( exception( status ) ) return status;
  }

  TomowindowCorrParam window = TomowindowCorrParamInitializer;
  MaskParam mask = MaskParamInitializer;
  PeakParam peak = PeakParamInitializer;
  CcfParam ccf = CcfParamInitializer;
  Size dim = 2;

  param = "area";
  status = TomoparamReadScalarCoord( tomoparam, param, &window.area );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( window.area > 1 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  status = TomoparamCCF( tomoparam, "correlation", &ccf );
  if ( exception( status ) ) retstat = status;
  if ( ccf.mode ) window.ccmode = ccf.mode;

  param = "correlation.size";
  status = TomoparamReadArraySize( tomoparam, param, window.corlen, 2, NULL );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( !window.corlen[0] || !window.corlen[1] ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  param = "correlation.median";
  status = TomoparamReadScalarSize( tomoparam, param, &window.cormed );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "correlation.flatfieldcorrection";
  status = TomoparamReadScalarSize( tomoparam, param, &window.corflt );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  status = TomoparamMask( tomoparam, "mask", &dim, &mask, TomoparamMaskNormal );
  if ( exception( status ) ) retstat = status;

  status = TomoparamPeak( tomoparam, "peaksearch", &dim, &peak );
  if ( exception( status ) ) retstat = status;

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) goto error1;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error1;
  }

  if ( mask.flags & MaskFunctionMask ) {
    MaskParam *ptr = MaskParamNew( &window.msk );
    if ( ptr == NULL ) { status = exception( E_MALLOC ); goto error2; }
    *ptr = mask;
  }
  if ( peak.flags & PeakParamDefined ) {
    window.pk = malloc( sizeof(*window.pk) );
    if ( window.pk == NULL ) { status = exception( E_MALLOC ); goto error2; }
    *window.pk = peak;
  }

  *tomowindowcorrparam = window;

  return E_NONE;

  error2: if ( window.msk != NULL ) free( window.msk );
  error1: TomoparamPeakFinal( &peak );
          TomoparamMaskFinal( &mask );
  return status;

}


extern Status TomowindowParamFinal
              (TomowindowParam *tomowindowparam)

{

  if ( tomowindowparam != NULL ) {

    TomoparamMaskParamFinal( (MaskParam *)tomowindowparam->msk );
    TomoparamMaskParamFinal( (MaskParam *)tomowindowparam->flt );

    if ( tomowindowparam->msk != NULL ) free( tomowindowparam->msk );
    if ( tomowindowparam->flt != NULL ) free( tomowindowparam->flt );

  }

  *tomowindowparam = TomowindowParamInitializer;

  return E_NONE;

}


extern Status TomowindowCorrParamFinal
              (TomowindowCorrParam *tomowindowcorrparam)

{

  if ( tomowindowcorrparam != NULL ) {

    TomoparamMaskParamFinal( tomowindowcorrparam->msk );
    TomoparamPeakFinal( tomowindowcorrparam->pk );

    if ( tomowindowcorrparam->msk != NULL ) free( tomowindowcorrparam->msk );
    if ( tomowindowcorrparam->pk  != NULL ) free( tomowindowcorrparam->pk );

  }

  *tomowindowcorrparam = TomowindowCorrParamInitializer;

  return E_NONE;

}
