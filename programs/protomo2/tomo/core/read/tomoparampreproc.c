/*----------------------------------------------------------------------------*
*
*  tomoparampreproc.c  -  core: retrieve parameters
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
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomoparamPreproc
              (Tomoparam *tomoparam,
               const char *ident,
               const PreprocParam *paramdefault,
               Size *dimptr,
               PreprocParam *preprocparam)

{
  const char *sect;
  const char *param;
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dimptr == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( preprocparam == NULL ) ) return pushexception( E_ARGVAL );

  *preprocparam = PreprocParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  Size dim = *dimptr;
  PreprocParam preproc = ( paramdefault == NULL ) ? PreprocParamInitializer : *paramdefault;
  const Coord *rad = preproc.rad;
  const Size *kernel = preproc.kernel;
  Bool boolval;
  char *filt;
  Coord val[3];
  Size kern[3];
  const char *fpar = NULL;

  param = "logging";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      preproc.flags |= PreprocLog;
    }
  }

  param = "filter";
  status = TomoparamReadScalarString( tomoparam, param, &filt );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      fpar = param;
      if ( !strcmp( filt, "min" ) ) {
        preproc.flags |= PreprocMin;
      } else if ( !strcmp( filt, "max" ) ) {
        preproc.flags |= PreprocMax;
      } else if ( !strcmp( filt, "mean" ) ) {
        preproc.flags |= PreprocMean;
      } else if ( !strcmp( filt, "median" ) ) {
        preproc.flags |= PreprocMedian;
      } else if ( !strcmp( filt, "gauss" ) ) {
        preproc.flags |= PreprocGauss;
      } else {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
        fpar = NULL;
      }
      free( filt );
    }
  }

  param = "gradient";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      if ( boolval ) preproc.flags |= PreprocGrad;
    }
  }

  param = "iter";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      if ( boolval ) preproc.flags |= PreprocGrad | PreprocIter;
    }
  }

  param = "thr";
  status = TomoparamReadArrayCoord( tomoparam, param, val, 2, NULL );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      preproc.thrmin = val[0];
      preproc.thrmax = val[1];
      preproc.flags |= PreprocThr;
    }
  }

  param = "clip";
  status = TomoparamReadArrayCoord( tomoparam, param, val, 2, NULL );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      preproc.clipmin = val[0];
      preproc.clipmax = val[1];
      preproc.flags |= PreprocClip;
    }
  }

  param = "grow";
  status = TomoparamReadScalarSize( tomoparam, param, &preproc.grow );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "radius";
  status = TomoparamReadArrayCoord( tomoparam, param, val, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ( preproc.flags & PreprocFunc ) != PreprocGauss ) {
      retstat = TomoparamReadErrorConflict( sect, param, fpar );
    } else {
      rad = val;
    }
  }

  param = "kernel";
  status = TomoparamReadArraySize( tomoparam, param, kern, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      boolval = True;
      for ( Size i = 0; i < dim; i++ ) {
        if ( kern[i] < 3 ) {
          retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
          boolval = False;
          break;
        }
      }
      if ( boolval ) kernel = kern;
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat ) {

    if ( rad != NULL ) {
      Size size = dim * sizeof(Coord);
      Coord *ptr = malloc( size );
      if ( ptr == NULL ) { status = pushexception( E_MALLOC ); goto error1; }
      memcpy( ptr, rad, size );
      rad = ptr;
    }
    if ( kernel != NULL ) {
      Size size = dim * sizeof(Size);
      Size *ptr = malloc( size );
      if ( ptr == NULL ) { status = pushexception( E_MALLOC ); goto error2; }
      memcpy( ptr, kernel, size );
      kernel = ptr;
    }

    preproc.rad = rad;
    preproc.kernel = kernel;

    *preprocparam = preproc;

    *dimptr = dim;

  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

  error2: if ( rad != NULL ) free( (Coord *)rad );
  error1: return status;

}


extern Status TomoparamPreprocFinal
              (PreprocParam *preprocparam)

{

  if ( preprocparam != NULL ) {

    if ( preprocparam->kernel != NULL ) free( (Size *)preprocparam->kernel );
    if ( preprocparam->rad != NULL ) free( (Coord *)preprocparam->rad );
    *preprocparam = PreprocParamInitializer;
  }

  return E_NONE;

}
