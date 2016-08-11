/*----------------------------------------------------------------------------*
*
*  tomowindowcorr.c  -  align: image windows
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
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status TomowindowCorr
              (const Tomowindow *window,
               const Cmplx *refaddr,
               Real refpwr,
               const Cmplx *fouaddr,
               const Real *foupwr,
               Cmplx *ccfaddr,
               Real *coraddr,
               Real *cornorm,
               Coord *pos,
               Real *pk)

{
  Real norm;
  Status status;

  if ( argcheck( window == NULL ) ) return exception( E_ARGVAL );

  const WindowFourier *fou = &window->fou;

  status = WindowCcf( fou, refaddr, fouaddr, ccfaddr, NULL, coraddr );
  if ( exception( status ) ) return status;

  if ( window->cormed > 1 ) {
    status = TomowindowCorrMedian( fou->img.dim, fou->img.len, coraddr, (Real *)ccfaddr, window->cormed );
    if ( exception( status ) ) return status;
  }

  if ( window->corflt > 0 ) {
    status = TomowindowCorrFlt( fou->img.dim, fou->img.len, pos, coraddr, window->corflt );
    if ( exception( status ) ) return status;
  }

  status = WindowPeak( fou, coraddr, pos, pk );
  if ( exception( status ) ) return status;

  if ( foupwr != NULL ) {
    if ( cornorm == NULL ) cornorm = &norm;
    *cornorm = FnSqrt( refpwr * *foupwr );
    if ( pk != NULL ) *pk = ( *cornorm > 0 ) ? *pk / *cornorm : 0;
  }

  return E_NONE;

}
