/*----------------------------------------------------------------------------*
*
*  windowalignregister.c  -  fourierop: window alignment
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

extern Status WindowAlignRegister
              (const WindowAlign *align,
               const Size *len,
               Type type,
               const void *addr,
               const Coord *A,
               const Coord *b,
               Real *winaddr,
               const MaskParam *winmsk,
               const Cmplx *refaddr,
               Real refpwr,
               Cmplx *fouaddr,
               Real *foupwr,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr,
               Real *cornorm,
               Coord *pos,
               Real *pk)

{
  Real norm;
  Stat winstat;
  Status status;

  if ( argcheck( align == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( len   == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( refaddr == NULL ) ) return exception( E_ARGVAL );

  const Window *win = &align->win;
  const WindowFourier *fou = &align->fou;

  Real *winbuf = NULL;
  if ( coraddr == NULL ) {
    winbuf = WindowAlloc( win );
    if ( winbuf == NULL ) return exception( E_MALLOC );
    if ( winaddr == NULL ) winaddr = winbuf;
    coraddr = winbuf;
  } else {
    if ( winaddr == NULL ) winaddr = coraddr;
  }

  status = WindowResample( len, type, addr, A, b, &align->win, winaddr, &winstat, winmsk );
  if ( exception( status ) ) goto exit1;

  Cmplx *foubuf = NULL;
  if ( fouaddr == NULL ) {
    foubuf = WindowFourierAlloc( fou );
    if ( foubuf == NULL ) return exception( E_MALLOC );
    fouaddr = foubuf;
  }

  status = WindowTransform( fou, winaddr, fouaddr, foupwr, NULL );
  if ( exception( status ) ) goto exit2;

  status = WindowCcf( fou, refaddr, fouaddr, ccfaddr, ccfflt, coraddr );
  if ( exception( status ) ) goto exit2;

  status = WindowPeak( fou, coraddr, pos, pk );
  if ( exception( status ) ) goto exit2;

  if ( foupwr != NULL ) {
    if ( cornorm == NULL ) cornorm = &norm;
    *cornorm = FnSqrt( refpwr * *foupwr );
    if ( pk != NULL ) *pk = ( *cornorm > 0 ) ? *pk / *cornorm : 0;
  }

  exit2: if ( foubuf != NULL ) free( foubuf );
  exit1: if ( winbuf != NULL ) free( winbuf );

  return status;

}
