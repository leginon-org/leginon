/*----------------------------------------------------------------------------*
*
*  tomoparammask.c  -  core: retrieve parameters
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

extern Status TomoparamMask
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               MaskParam *maskparam,
               TomoparamMode mode)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dimptr == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( maskparam == NULL ) ) return pushexception( E_ARGVAL );

  *maskparam = MaskParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  Size dim = *dimptr;
  MaskParam mask = MaskParamInitializer;
  Transform transform = TransformInitializer;
  const char *wpar = NULL; Coord wbuf[3];
  const char *apar = NULL; Coord abuf[3];
  const char *mpar = NULL;
  char *unit = NULL;

  param = "inv";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( mode & ( TomoparamMaskNormal | TomoparamMaskInv ) ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    } else if ( boolval ) {
      mask.flags |= MaskModeInv;
    }
  }
  if ( mode & TomoparamMaskInv ) {
    mask.flags |= MaskModeInv;
  }

  param = "mean";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( mode & TomoparamMaskFourier ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    } else {
      if ( boolval ) mask.flags |= MaskModeAuto;
      mpar = param;
    }
  }

  param = "width";
  status = TomoparamReadArrayCoord( tomoparam, param, wbuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( mode & TomoparamMaskFourier ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    } else {
      for ( Size i = 0; i < dim; i++ ) {
        if ( wbuf[i] < 0 ) {
          retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL ); break;
        }
        if ( wbuf[i] > 0 ) {
          mask.flags |= MaskFunctionRect;
          wpar = param;
        }
      }
    }
  }

  param = "diameter";
  status = TomoparamReadArrayCoord( tomoparam, param, wbuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( wpar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, param, wpar );
    } else {
      for ( Size i = 0; i < dim; i++ ) {
        if ( wbuf[i] < 0 ) {
          retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL ); break;
        }
        if ( wbuf[i] > 0 ) {
          mask.flags |= MaskFunctionEllips;
          wpar = param;
        }
      }
    }
  }

  param = "sigma";
  status = TomoparamReadArrayCoord( tomoparam, param, wbuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( wpar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, param, wpar );
    } else {
      for ( Size i = 0; i < dim; i++ ) {
        if ( wbuf[i] < 0 ) {
          retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL ); break;
        }
        if ( wbuf[i] > 0 ) {
          mask.flags |= MaskFunctionGauss;
          wpar = param;
        }
      }
    }
  }

  param = "apodization";
  status = TomoparamReadArrayCoord( tomoparam, param, abuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ( wpar == NULL ) || ( *wpar == 's' ) ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    } else {
      for ( Size i = 0; i < dim; i++ ) {
        if ( abuf[i] < 0 ) {
          retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL ); break;
        }
        if ( abuf[i] > 0 ) {
          mask.flags |= MaskModeApod;
          apar = param;
        }
      }
    }
  }

  param = "unit";
  status = TomoparamReadScalarString( tomoparam, param, &unit );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      if ( !strcmp( unit, "pixel" ) ) {
        mask.flags |= MaskModeUnit | MaskModeNormal;
      } else if ( !strcmp( unit, "fract" ) ) {
        mask.flags |= MaskModeUnit | MaskModeFract;
      } else {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      }
      free( unit );
    }
  }

  param = "value";
  status = TomoparamReadScalarCoord( tomoparam, param, &mask.val );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( mpar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, param, mpar );
    } else if ( mode & TomoparamMaskFourier ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    } else {
      mask.flags |= MaskModeVal;
    }
  }

  status = TomoparamTransform( tomoparam, NULL, &dim, &transform, !( mode & TomoparamMaskFourier ) );
  if ( exception( status ) ) return status;
  mask.A = transform.A;
  mask.b = transform.b;

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) goto error;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error;
  }

  if ( dim && ( mask.flags & MaskFunctionMask ) ) {

    Size size = dim * sizeof(Coord);
    if ( wpar != NULL ) {
      mask.wid = malloc( size );
      if ( mask.wid == NULL ) { status = pushexception( E_MALLOC ); goto error; }
      memcpy( mask.wid, wbuf, size );
    }
    if ( apar != NULL ) {
      mask.apo = malloc( size );
      if ( mask.apo == NULL ) { status = pushexception( E_MALLOC ); goto error; }
      memcpy( mask.apo, abuf, size );
    }

    *maskparam = mask;

    *dimptr = dim;

  }

  return E_NONE;

  error:
  TomoparamMaskFinal( &mask );
  return status;

}


extern Status TomoparamMaskWedge
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               MaskParam *maskparam,
               TomoparamMode mode)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( ident == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dimptr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( maskparam == NULL ) ) return exception( E_ARGVAL );

  *maskparam = MaskParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  /* 3d only */
  Size dim = *dimptr;
  if ( dim && ( dim != 3 ) ) {
    status = TomoparamReadError( sect, NULL, E_TOMOPARAMREAD_SEC );
    return exception( status );
  }

  MaskParam mask = MaskParamInitializer;
  Transform transform = TransformInitializer;
  const char *wpar = NULL; Coord wbuf[3];
  const char *mpar = NULL;
  Coord  apo = 0;

  param = "inv";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( mode & ( TomoparamMaskNormal | TomoparamMaskInv ) ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    } else {
      if ( boolval ) mask.flags |= MaskModeInv;
      dim = 3;
    }
  }

  param = "mean";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( mode & TomoparamMaskFourier ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    } else {
      if ( boolval ) mask.flags |= MaskModeAuto;
      mpar = param;
      dim = 3;
    }
  }

  param = "range";
  status = TomoparamReadArrayCoord( tomoparam, param, wbuf, 2, NULL );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ( wbuf[0] < -90 ) || ( wbuf[1] > 90 ) || ( wbuf[0] >= wbuf[1] ) ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      mask.flags |= MaskFunctionWedge;
      wpar = param;
      dim = 3;
    }
  }

  param = "apodization";
  status = TomoparamReadScalarCoord( tomoparam, param, &apo );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( apo < 0 ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    } else {
      mask.flags |= MaskModeApod;
      dim = 3;
    }
  }

  param = "value";
  status = TomoparamReadScalarCoord( tomoparam, param, &mask.val );
  if ( status ) {
    retstat = TomoparamReadError( sect, param, status );
  } else if ( mpar != NULL ) {
    retstat = TomoparamReadErrorConflict( sect, param, mpar );
  } else if ( mode & TomoparamMaskFourier ) {
    retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
  } else {
    mask.flags |= MaskModeVal;
    dim = 3;
  }

  status = TomoparamTransform( tomoparam, NULL, &dim, &transform, !( mode & TomoparamMaskFourier ) );
  if ( exception( status ) ) return status;
  mask.A = transform.A;
  mask.b = transform.b;

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) goto error;
  }

  if ( retstat ) {
    status = E_TOMOPARAMREAD_ERROR; goto error;
  }

  if ( dim && ( mask.flags & MaskFunctionMask ) ) {

    Size size = dim * sizeof(Coord);
    if ( wpar != NULL ) {
      mask.wid = malloc( size );
      if ( mask.wid == NULL ) { status = pushexception( E_MALLOC ); goto error; }
      mask.wid[0] = wbuf[0] * Pi / 180;
      mask.wid[1] = wbuf[1] * Pi / 180;
      mask.wid[2] = apo;
    }

    *maskparam = mask;

    *dimptr = dim;

  }

  return E_NONE;

  error:
  TomoparamMaskFinal( &mask );
  return status;

}


extern Status TomoparamMaskFinal
              (MaskParam *maskparam)

{

  if ( maskparam != NULL ) {

    if ( maskparam->A != NULL ) free( maskparam->A );
    if ( maskparam->b != NULL ) free( maskparam->b );
    if ( maskparam->wid != NULL ) free( maskparam->wid );
    if ( maskparam->apo != NULL ) free( maskparam->apo );
    *maskparam = MaskParamInitializer;

  }

  return E_NONE;

}


extern Status TomoparamMaskParamFinal
              (MaskParam *maskparam)

{

  if ( maskparam != NULL ) {

    while ( maskparam->flags & MaskFunctionMask ) {
      TomoparamMaskFinal( maskparam++ );
    }

  }

  return E_NONE;

}
