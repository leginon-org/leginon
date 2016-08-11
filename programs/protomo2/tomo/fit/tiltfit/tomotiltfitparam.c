/*----------------------------------------------------------------------------*
*
*  tomotiltfitparam.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotiltfit.h"
#include "tomoparamread.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status TomotiltFitGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomotiltFitParam *fitparam)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Size sizeval;
  Status status, retstat = E_NONE;

  *fitparam = TomotiltFitParamInitializer;
  Bool global;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  TomotiltFitParam fit = TomotiltFitParamInitializer;

  param = "globalorientation";
  status = TomoparamReadScalarBool( tomoparam, param, &global );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  } else {
    global = True;
  }

  param = "orientation";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      fit.flags |= TomotiltFitOrient;
      if ( global ) fit.flags |= TomotiltFitEuler;
    }
  }

  param = "azimuth";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      fit.flags |= TomotiltFitAzim;
    }
  }

  param = "elevation";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      fit.flags |= TomotiltFitElev;
    }
  }

  param = "angleoffset";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      fit.flags |= TomotiltFitOffs;
    }
  }

  param = "angle";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      fit.flags |= TomotiltFitTheta;
    }
  }

  param = "rotation";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      fit.flags |= TomotiltFitAlpha;
    }
  }

  param = "scale";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      fit.flags |= TomotiltFitScale;
    }
  }

  param = "select";
  status = TomoparamReadSelection( tomoparam, param, &fit.selection );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "exclude";
  status = TomoparamReadSelection( tomoparam, param, &fit.exclusion );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "det";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      fit.flags |= TomotiltFitDet;
    }
  }

  param = "logging";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      fit.flags |= TomotiltFitLog;
    }
  }

  param = "loglevel";
  status = TomoparamReadScalarSize( tomoparam, param, &sizeval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( sizeval ) {
      fit.flags |= TomotiltFitLog;
      if ( sizeval > 1 ) fit.flags |= TomotiltFitDat;
      if ( sizeval > 2 ) fit.flags |= TomotiltFitDbg;
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) goto error;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error;
  }

  *fitparam = fit;

  return E_NONE;

  error: if ( fit.selection != NULL ) free( fit.selection );

  return status;

}


extern Status TomotiltFitParamFinal
              (TomotiltFitParam *fitparam)

{

  if ( fitparam != NULL ) {

    if ( fitparam->selection != NULL ) {
      free( (Size *)fitparam->selection ); fitparam->selection = NULL;
    }
    if ( fitparam->exclusion != NULL ) {
      free( (Size *)fitparam->exclusion ); fitparam->exclusion = NULL;
    }

  }

  return E_NONE;

}
