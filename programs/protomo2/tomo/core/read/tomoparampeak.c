/*----------------------------------------------------------------------------*
*
*  tomoparampeak.c  -  core: retrieve parameters
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

extern Status TomoparamPeak
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               PeakParam *peakparam)

{
  const char *sect;
  const char *param;
  Bool boolval;
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dimptr == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( peakparam == NULL ) ) return pushexception( E_ARGVAL );

  *peakparam = PeakParamInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  Size dim = *dimptr;
  const char *epar = NULL;
  Bool pk = False; Coord *pkrad = NULL; Coord pkbuf[3];
  Bool cm = False; Coord *cmrad = NULL; Coord cmbuf[3];
  PeakFlags flags = PeakOriginRelative | PeakModeCyc;

  param = "height";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      flags |= PeakHeightInterp;
    }
  }

  param = "radius";
  status = TomoparamReadArrayCoord( tomoparam, param, pkbuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      pk = True;
    }
  }

  param = "cmdiameter";
  status = TomoparamReadArrayCoord( tomoparam, param, cmbuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      flags |= PeakCMEllips;
      cm = True;
      epar = param;
    }
  }

  param = "cmwidth";
  status = TomoparamReadArrayCoord( tomoparam, param, cmbuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( epar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, param, epar );
    } else {
      cm = True;
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat && dim ) {

    Size size = dim * sizeof(Coord);
    if ( pk ) {
      pkrad = malloc( size );
      if ( pkrad == NULL ) { status = pushexception( E_MALLOC ); goto error1; }
      memcpy( pkrad, pkbuf, size );
    }
    if ( cm ) {
      cmrad = malloc( size );
      if ( cmrad == NULL ) { status = pushexception( E_MALLOC ); goto error2; }
      memcpy( cmrad, cmbuf, size );
    }

    if ( pk )  peakparam->rad = pkrad;
    if ( cm )  peakparam->cmrad = cmrad;
    peakparam->flags = flags | PeakParamDefined;

    *dimptr = dim;

  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

  error2: if ( pkrad != NULL ) free( pkrad );
  error1: return status;

}


extern Status TomoparamPeakFinal
              (PeakParam *peakparam)

{

  if ( peakparam != NULL ) {

    if ( peakparam->ctr != NULL ) free( peakparam->ctr );
    if ( peakparam->rad != NULL ) free( peakparam->rad );
    if ( peakparam->cmrad != NULL ) free( peakparam->cmrad );
    *peakparam = PeakParamInitializer;
  }

  return E_NONE;

}
