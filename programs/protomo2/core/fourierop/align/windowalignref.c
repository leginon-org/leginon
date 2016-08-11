/*----------------------------------------------------------------------------*
*
*  windowalignref.c  -  fourierop: window alignment
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
#include <stdlib.h>


/* functions */

extern Status WindowAlignRef
              (const WindowAlign *align,
               const Size *len,
               Type type,
               const void *addr,
               const Coord *A,
               const Coord *b,
               Real *winaddr,
               const MaskParam *winmsk,
               Cmplx *refaddr,
               Real *refpwr,
               const MaskParam *refflt)

{
  Stat winstat;
  Status status;

  if ( argcheck( align == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( len   == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( refaddr == NULL ) ) return exception( E_ARGVAL );

  const Window *win = &align->win;
  const WindowFourier *fou = &align->fou;

  Real *winbuf = NULL;
  if ( winaddr == NULL ) {
    winbuf = WindowAlloc( win );
    if ( winbuf == NULL ) return exception( E_MALLOC );
    winaddr = winbuf;
  }

  status = WindowResample( len, type, addr, A, b, win, winaddr, &winstat, winmsk );
  if ( exception( status ) ) goto exit;

  status = WindowTransform( fou, winaddr, refaddr, refpwr, refflt );
  if ( exception( status ) ) goto exit;

  exit: if ( winbuf != NULL ) free( winbuf );

  return status;

}
