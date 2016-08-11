/*----------------------------------------------------------------------------*
*
*  tomoparamwindow.c  -  core: retrieve parameters
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

extern Status TomoparamWindow
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               Size *len,
               WindowParam *windowparam)

{
  const char *sect;
  const char *param;
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dimptr == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( len == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( windowparam == NULL ) ) return pushexception( E_ARGVAL );

  *windowparam = WindowParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, True );
    if ( exception( status ) ) return status;
  }

  Size dim = *dimptr;
  Size lbuf[3];
  Coord area = -1;

  param = "size";
  status = TomoparamReadArraySize( tomoparam, param, lbuf, 3, &dim );
  if ( status ) {
    retstat = TomoparamReadError( sect, param, status );
  } else {
    for ( Size i = 0; i < dim; i++ ) {
      if ( !lbuf[i] ) {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
        break;
      }
    }
  }

  param = "area";
  status = TomoparamReadScalarCoord( tomoparam, param, &area );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ( area < 0 ) || ( area > 1 ) ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat ) {
    windowparam->area = area;
    memcpy( len, lbuf, dim * sizeof(Size) );
    *dimptr = dim;
  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

}


extern Status TomoparamWindowFinal
              (WindowParam *windowparam)

{

  if ( windowparam != NULL ) {

    if ( windowparam->msk != NULL ) free( (MaskParam *)windowparam->msk );
    *windowparam = WindowParamInitializer;

  }

  return E_NONE;

}
