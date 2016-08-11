/*----------------------------------------------------------------------------*
*
*  tomoparamctf.c  -  core: retrieve parameters
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

extern Status TomoparamCtf
              (Tomoparam *tomoparam,
               const char *ident,
               ImageCTFParam *ctfparam)

{
  const char *sect;
  const char *param;
  const char *apar = NULL;
  const char *zpar = NULL;
  ImageCTFParam ctf;
  Coord val[2];
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( ctfparam == NULL ) ) return pushexception( E_ARGVAL );

  *ctfparam = ImageCTFParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, True );
    if ( exception( status ) ) return status;
  }

  /* defaults */
  ctf = ImageCTFParamInitializer;

  param = "pixel"; /* [nm] */
  status = TomoparamReadScalarCoord( tomoparam, param, &ctf.pixel );
  if ( status ) {
    retstat = TomoparamReadError( sect, param, status );
  } else if ( ctf.pixel <= 0 ) {
    retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    ctf.pixel = 0;
  }
  param = "ca";
  status = TomoparamReadScalarCoord( tomoparam, param, &ctf.ca );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ctf.ca <= 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      ctf.ca = 0;
    } else {
      apar = param;
    }
  }

  param = "phia"; /* [deg] */
  status = TomoparamReadScalarCoord( tomoparam, param, &ctf.phia );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "za"; /* [nm] */
  status = TomoparamReadArrayCoord( tomoparam, param, val, 2, NULL );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( apar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, param, apar );
    } else {
      ctf.dz = ( val[0] + val[1] ) / 2;
      ctf.ca = Fabs( ( val[1] - val[0] ) / ctf.dz );
      zpar = param;
    }
  }

  param = "defocus"; /* [nm] */
  status = TomoparamReadScalarCoord( tomoparam, param, val );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( zpar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, param, zpar );
    } else {
      ctf.dz = *val;
    }
  } else if ( zpar == NULL ) {
    retstat = TomoparamReadError( sect, param, E_TOMOPARAM_UNDEF );
  }

  param = "amplcontrast"; /* [deg] */
  status = TomoparamReadScalarCoord( tomoparam, param, &ctf.ampcon );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat ) {

    /* returned units: nm */
    ctfparam->pixel  = ctf.pixel;
    ctfparam->ca     = ctf.ca;
    ctfparam->phia   = ctf.phia * Pi / 180;
    ctfparam->dz     = ctf.dz;
    ctfparam->ampcon = ctf.ampcon * Pi / 180;

  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

}
