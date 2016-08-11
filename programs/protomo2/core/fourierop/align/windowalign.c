/*----------------------------------------------------------------------------*
*
*  windowalign.c  -  fourierop: window alignment
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

extern Status WindowAlignInit
              (Size dim,
               const Size *len,
               WindowAlign *align,
               const WindowAlignParam *param)

{
  Status status;

  if ( argcheck( len == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( align == NULL ) ) return exception( E_ARGVAL );

  const WindowParam *wpar = NULL;
  const WindowFourierParam *fpar = NULL;
  const MaskParam *foumsk = NULL;
  const MaskParam *fouflt = NULL;
  const PeakParam *pkpar = NULL;

  *align = WindowAlignInitializer;

  if ( param != NULL ) {
    wpar = &param->win;
    fpar = &param->fou;
    foumsk = param->foumsk;
    fouflt = param->fouflt;
    pkpar  = param->pkpar;
    align->winmsk = param->winmsk;
  }

  status = WindowFourierInit( dim, len, foumsk, fouflt, pkpar, &align->fou, fpar );
  if ( exception( status ) ) return status;

  status = WindowInit( dim, align->fou.img.len, &align->win, wpar );
  if ( exception( status ) ) {
    WindowFourierFinal( &align->fou );
    return status;
  }

  return E_NONE;

}


extern Status WindowAlignFinal
              (WindowAlign *align)

{
  Status status;

  if ( align != NULL ) {

    status = WindowFourierFinal( &align->fou );
    if ( exception( status ) ) return status;

    *align = WindowAlignInitializer;

  }

  return E_NONE;

}
