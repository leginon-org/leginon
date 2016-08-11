/*----------------------------------------------------------------------------*
*
*  tomoalignparam.c  -  align: series alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoaligncommon.h"
#include "tomoparamread.h"
#include "maskparam.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

static Status TomoalignGetGridParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomoalignGrid *gridparam)

{
  const char *sect;
  const char *param;
  TomoalignGrid grid;
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( gridparam == NULL ) ) return pushexception( E_ARGVAL );

  *gridparam = TomoalignGridInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  grid = TomoalignGridInitializer;

  param = "step";
  status = TomoparamReadScalarCoord( tomoparam, param, &grid.step );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( grid.step < 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    }
  }

  param = "limit";
  status = TomoparamReadScalarCoord( tomoparam, param, &grid.limit );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( grid.limit < 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat ) {
    *gridparam = grid;
  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

}


extern Status TomoalignGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomoalignParam *alignparam)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Status status, retstat = E_NONE;

  *alignparam = TomoalignParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  TomoalignParam align = TomoalignParamInitializer;
  const char *rpar = NULL;

  param = "logging";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      align.flags |= TomoLog;
    }
  }

  param = "restart";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      align.flags |= TomoRestart;
      rpar = param;
    }
  }

  param = "estimate";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      align.flags |= TomoflagEstimate;
    }
  }

  param = "norotations";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      align.flags |= TomoflagZeroRot;
    }
  }

  param = "select";
  status = TomoparamReadSelection( tomoparam, param, &align.selection );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "exclude";
  status = TomoparamReadSelection( tomoparam, param, &align.exclusion );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "startimage";
  status = TomoparamReadScalarSize( tomoparam, param, &align.startimage );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( rpar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, param, rpar );
    }
  }

  param = "startangle";
  status = TomoparamReadScalarCoord( tomoparam, param, &align.startangle );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ( align.startangle < 0 ) || ( align.startangle >= 90 ) ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  param = "maxtilt";
  status = TomoparamReadScalarCoord( tomoparam, param, &align.maxangle );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ( align.maxangle <= 0 ) || ( align.maxangle >= 90 ) ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  param = "maxshift";
  status = TomoparamReadScalarCoord( tomoparam, param, &align.maxshift );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( align.maxshift <= 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  param = "maxcorrection";
  status = TomoparamReadScalarCoord( tomoparam, param, &align.maxcorr );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( align.maxcorr <= 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  param = "translimit";
  status = TomoparamReadScalarCoord( tomoparam, param, &align.transmax );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( align.transmax < 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  status = TomowindowCorrGetParam( tomoparam, NULL, &align.corr );
  if ( exception( status ) ) retstat = status;

  status = TomoalignGetGridParam( tomoparam, "gridsearch", &align.grid );
  if ( exception( status ) ) retstat = status;

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) goto error;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error;
  }

  *alignparam = align;

  return E_NONE;

  error:
  TomowindowCorrParamFinal( &align.corr );
  if ( align.selection != NULL ) free( align.selection );
  if ( align.exclusion != NULL ) free( align.exclusion );
  return status;

}


extern Status TomoalignParamFinal
              (TomoalignParam *alignparam)

{

  if ( alignparam != NULL ) {

    TomowindowCorrParamFinal( &alignparam->corr );

    if ( alignparam->selection != NULL ) free( alignparam->selection );
    if ( alignparam->exclusion != NULL ) free( alignparam->exclusion );

    *alignparam = TomoalignParamInitializer;

  }

  return E_NONE;

}
