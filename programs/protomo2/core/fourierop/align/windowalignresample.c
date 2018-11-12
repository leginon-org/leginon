/*----------------------------------------------------------------------------*
*
*  windowalignresample.c  -  fourierop: window alignment
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


/* functions */

extern Status WindowAlignResample
              (const WindowAlign *align,
               const Size *len,
               Type type,
               const void *addr,
               const Coord *A,
               const Coord *b,
               Real *winaddr,
               Stat *winstat,
               const MaskParam *winmsk)

{
  Status status;

  if ( argcheck( align == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( len   == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr  == NULL ) ) return exception( E_ARGVAL );

  status = WindowResample( len, type, addr, A, b, &align->win, winaddr, winstat, winmsk );
  logexception( status );

  return status;

}
