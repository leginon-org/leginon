/*----------------------------------------------------------------------------*
*
*  windowalignccf.c  -  fourierop: window alignment
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

extern Status WindowAlignCcf
              (const WindowAlign *align,
               const Cmplx *refaddr,
               const Cmplx *fouaddr,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr)

{
  Status status = E_NONE;

  if ( argcheck( align == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( refaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( fouaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( coraddr == NULL ) ) return exception( E_ARGVAL );

  const WindowFourier *fou = &align->fou;

  Cmplx *ccfbuf = NULL;
  if ( ccfaddr == NULL ) {
    ccfbuf = WindowFourierAlloc( fou );
    if ( ccfbuf == NULL ) return exception( E_MALLOC );
    ccfaddr = ccfbuf;
  }

  status = WindowCcf( fou, refaddr, fouaddr, ccfaddr, ccfflt, coraddr );
  logexception( status );

  if ( ccfbuf != NULL ) free( ccfbuf );

  return status;

}
