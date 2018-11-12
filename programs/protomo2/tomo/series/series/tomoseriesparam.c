/*----------------------------------------------------------------------------*
*
*  tomoseriesparam.c  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseries.h"
#include "tomoparamread.h"
#include "strings.h"
#include "thread.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

static Status TomoseriesPreprocFinal
              (Tomodatapreproc *preproc)

{

  TomoparamPreprocFinal( &preproc->main );
  TomoparamPreprocFinal( &preproc->mask );
  *preproc = TomodatapreprocInitializer;

  return E_NONE;

}


extern Status TomoseriesGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomoseriesParam *seriesparam)

{
  const char *sect, *subsect;
  const char *param;
  char *string;
  Bool boolval;
  Size dim = 2;
  Status status, retstat = E_NONE;

  *seriesparam = TomoseriesParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  TomoseriesParam series = TomoseriesParamInitializer;
  Tomodatapreproc preproc = TomodatapreprocInitializer;
  Transform transform = TransformInitializer;
  ImageioParam ioparam = ImageioParamDefault;

  param = "logging";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      series.flags |= TomoLog;
    }
  }

  param = "preprocessing";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      series.flags |= TomoPreproc;
    }
  }

  subsect = "preprocess";

  status = TomoparamReadPush( tomoparam, subsect, &sect, False );
  if ( exception( status ) ) { retstat = status; goto exit; }

  if ( sect != NULL ) {

    status = TomoparamPreproc( tomoparam, NULL, NULL, &dim, &preproc.main );
    if ( exception( status ) ) retstat = status;

    status = TomoparamPreproc( tomoparam, "mask", &preproc.main, &dim, &preproc.mask );
    if ( exception( status ) ) retstat = status;

    param = "border";
    status = TomoparamReadScalarSize( tomoparam, param, &preproc.border );
    if ( status != E_TOMOPARAM_UNDEF ) {
      if ( status ) {
        retstat = TomoparamReadError( sect, param, status );
      }
    }

    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) { retstat = status; goto exit; }

  }

  param = "binning";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      series.flags |= TomoSmp;
    }
  }

  param = "sampling";
  status = TomoparamReadScalarCoord( tomoparam, param, &series.sampling );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( series.sampling < 1 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  param = "prefix";
  status = TomoparamReadScalarString( tomoparam, param, &string );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( !*string ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      series.prfx = string;
    }
  } else {
    series.prfx = TomoparamGetPrfx( tomoparam );
  }

  param = "pathlist";
  status = TomoparamReadScalarString( tomoparam, param, &string );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( !*string ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      series.data.pathlist = string;
    }
  }

  param = "suffix";
  status = TomoparamReadScalarString( tomoparam, param, &string );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( !*string ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      series.data.imgsffx = string;
    }
  }

  param = "cacheprefix";
  status = TomoparamReadScalarString( tomoparam, param, &string );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( !*string ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      series.data.cacheprfx = string;
    }
  }

  param = "cachedir";
  status = TomoparamReadScalarString( tomoparam, param, &string );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( !*string ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      series.cachedir = string;
    }
  }

  param = "outdir";
  status = TomoparamReadScalarString( tomoparam, param, &string );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( !*string ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      series.outdir = string;
    }
  }

  param = "select";
  status = TomoparamReadSelection( tomoparam, param, &series.selection );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  param = "exclude";
  status = TomoparamReadSelection( tomoparam, param, &series.exclusion );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    }
  }

  status = TomoparamImageio( tomoparam, "input", &ioparam );
  if ( exception( status ) ) retstat = status;

  status = TomoparamTransform3( tomoparam, NULL, &transform );
  if ( exception( status ) ) retstat = status;
  series.A = transform.A;
  series.b = transform.b;

  Size proc;
  param = "processors";
  status = TomoparamReadScalarSize( tomoparam, param, &proc );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      ThreadSetCount( proc );
    }
  }

  exit:

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) goto error;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error;
  }

  Tomodatapreproc *ptr = malloc( sizeof(Tomodatapreproc) );
  if ( ptr == NULL ) {
    status = E_MALLOC; goto error;
  }
  *ptr = preproc;

  series.data.preproc = ptr;
  series.data.format = ioparam.format;
  series.data.cap = ioparam.cap;

  *seriesparam = series;

  return E_NONE;

  error: TomoseriesParamFinal( &series );
         TomoparamImageioFinal( &ioparam );
         TomoseriesPreprocFinal( &preproc );

  return status;

}


extern Status TomoseriesParamFinal
              (TomoseriesParam *seriesparam)

{

  if ( seriesparam != NULL ) {

    if ( seriesparam->prfx != NULL ) free( (char *)seriesparam->prfx );
    if ( seriesparam->outdir != NULL ) free( (char *)seriesparam->outdir );
    if ( seriesparam->cachedir != NULL ) free( (char *)seriesparam->cachedir );
    if ( seriesparam->data.cacheprfx != NULL ) free( (char *)seriesparam->data.cacheprfx );
    if ( seriesparam->data.pathlist != NULL ) free( (char *)seriesparam->data.pathlist );
    if ( seriesparam->data.imgsffx != NULL ) free( (char *)seriesparam->data.imgsffx );
    if ( seriesparam->data.preproc != NULL ) {
      TomoseriesPreprocFinal( (Tomodatapreproc *)seriesparam->data.preproc );
      free( (Tomodatapreproc *)seriesparam->data.preproc );
    }
    if ( seriesparam->A != NULL ) free( (Coord *)seriesparam->A );
    if ( seriesparam->b != NULL ) free( (Coord *)seriesparam->b );
    if ( seriesparam->selection != NULL ) free( seriesparam->selection );
    if ( seriesparam->exclusion != NULL ) free( seriesparam->exclusion );
    *seriesparam = TomoseriesParamInitializer;

  }

  return E_NONE;

}
