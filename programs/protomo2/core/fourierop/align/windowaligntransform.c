/*----------------------------------------------------------------------------*
*
*  windowaligntransform.c  -  fourierop: window alignment
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

extern Status WindowAlignTransform
              (const WindowAlign *align,
               Real *winaddr,
               Cmplx *fouaddr,
               Real *foupwr,
               const MaskParam *fouflt)

{
  Status status;

  if ( argcheck( align == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( winaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( fouaddr == NULL ) ) return exception( E_ARGVAL );

  const WindowFourier *fou = &align->fou;

  status = WindowTransform( fou, winaddr, fouaddr, foupwr, fouflt );
  logexception( status );

  return status;

}
