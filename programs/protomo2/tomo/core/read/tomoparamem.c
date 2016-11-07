/*----------------------------------------------------------------------------*
*
*  tomoparamem.c  -  core: retrieve parameters
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

extern Status TomoparamEM
              (Tomoparam *tomoparam,
               const char *ident,
               EMparam *emparam)

{
  const char *sect;
  const char *param;
  const char *lpar = NULL;
  EMparam em;
  Coord val[2];
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( emparam == NULL ) ) return pushexception( E_ARGVAL );

  *emparam = EMparamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, True );
    if ( exception( status ) ) return status;
  }

  /* defaults */
  em = EMparamInitializer;
  em.lambda = LAMBDA( 300000 ) * 1e9;
  em.cs = 2.0e6;

  param = "lambda"; /* [nm] */
  status = TomoparamReadScalarCoord( tomoparam, param, &em.lambda );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( em.lambda <= 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      em.lambda = 0;
    } else {
      lpar = param;
    }
  }

  param = "U"; /* [V]  */
  status = TomoparamReadScalarCoord( tomoparam, param, val );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( *val <= 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else if ( lpar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, param, lpar );
    } else {
      em.lambda = LAMBDA( *val ) * 1e9;
    }
  }

  param = "cs"; /* [mm] */
  status = TomoparamReadScalarCoord( tomoparam, param, &em.cs );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( em.cs <= 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      em.cs = 0;
    }
  }

  param = "divergence"; /* [mrad] */
  status = TomoparamReadScalarCoord( tomoparam, param, &em.beta );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "focusspread"; /* [nm] */
  status = TomoparamReadScalarCoord( tomoparam, param, &em.fs );
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
    emparam->lambda = em.lambda;
    emparam->cs     = em.cs * 1e6;
    emparam->beta   = em.beta;
    emparam->fs     = em.fs;

  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

}
