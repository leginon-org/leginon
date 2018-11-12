/*----------------------------------------------------------------------------*
*
*  windowpeak.c  -  window: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "windowfourier.h"
#include "exception.h"


/* variables */

static Coord WindowPeakRad[] = { -1.0, -1.0, -1.0 };
static Coord WindowPeakCMRad[] = { 1.0, 1.0, 1.0 };

static const PeakParam WindowPeakParamDefault = {
  NULL,
  WindowPeakRad,
  WindowPeakCMRad,
  PeakOriginRelative | PeakModeCyc | PeakCMEllips,
};


/* functions */

extern Status WindowPeak
              (const WindowFourier *win,
               const Real *addr,
               Coord *pos,
               Real *pk)


{
  PeakParam pkpar;
  Size ipos[3];
  Status status;

  if ( argcheck( win == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );

  /* defaults */
  if ( win->pkpar == NULL ) {
    pkpar = WindowPeakParamDefault;
  } else {
    pkpar = *win->pkpar;
    if ( pkpar.rad == NULL ) pkpar.rad = WindowPeakRad;
    if ( pkpar.cmrad == NULL ) pkpar.cmrad = WindowPeakCMRad;
  }

  Size dim = win->img.dim;

  status = PeakReal( dim, win->img.len, addr, ipos, pos, pk, &pkpar );
  if ( exception( status ) ) return status;

  if ( win->mode == CC_DBL ) {
    for ( Size d = 0; d < dim; d++ ) {
      pos[d] /= 2; /* shifts are doubled for phase doubled CCF */
    }
  }

  return E_NONE;

}
