/*----------------------------------------------------------------------------*
*
*  windowaligncorr.c  -  fourierop: window alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "windowalign.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* functions */

extern Status WindowAlignCorr
              (const WindowAlign *align,
               const Cmplx *refaddr,
               Real refpwr,
               const Cmplx *fouaddr,
               Real *foupwr,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr,
               Real *cornorm,
               Coord *pos,
               Real *pk)

{
  Real norm;
  Status status;

  if ( argcheck( align == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( refaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( fouaddr == NULL ) ) return exception( E_ARGVAL );

  const Window *win = &align->win;
  const WindowFourier *fou = &align->fou;

  Real *corbuf = NULL;
  if ( coraddr == NULL ) {
    corbuf = WindowAlloc( win );
    if ( corbuf == NULL ) return exception( E_MALLOC );
    coraddr = corbuf;
  }

  status = WindowCcf( fou, refaddr, fouaddr, ccfaddr, ccfflt, coraddr );
  if ( exception( status ) ) goto exit;

  status = WindowPeak( fou, coraddr, pos, pk );
  if ( exception( status ) ) goto exit;

  if ( foupwr != NULL ) {
    if ( cornorm == NULL ) cornorm = &norm;
    *cornorm = FnSqrt( refpwr * *foupwr );
    if ( pk != NULL ) *pk = ( *cornorm > 0 ) ? *pk / *cornorm : 0;
  }

  exit: if ( corbuf != NULL ) free( corbuf );

  return status;

}
