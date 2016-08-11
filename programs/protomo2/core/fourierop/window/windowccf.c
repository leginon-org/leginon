/*----------------------------------------------------------------------------*
*
*  windowccf.c  -  window: image windows
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
#include "imagemask.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* functions */

extern Status WindowCcf
              (const WindowFourier *win,
               const Cmplx *refaddr,
               const Cmplx *fouaddr,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr)


{
  Status status;

  if ( argcheck( win     == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( refaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( fouaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( coraddr == NULL ) ) return exception( E_ARGVAL );

  Cmplx *ccfbuf = NULL;
  if ( ccfaddr == NULL ) {
    ccfbuf = WindowFourierAlloc( win );
    if ( ccfbuf == NULL ) return exception( E_MALLOC );
    ccfaddr = ccfbuf;
  }

  status = CCFmodcalcCmplx( win->fousize, refaddr, fouaddr, ccfaddr, win->mode );
  if ( exception( status ) ) goto exit;

  if ( ccfflt != NULL ) {
    status = ImageMask( &win->fou, ccfaddr, NULL, NULL, ccfflt );
    if ( exception( status ) ) return status;
  }

  status = FourierInvRealTransf( win->back, ccfaddr, coraddr, 1 );
  if ( exception( status ) ) goto exit;

  exit: if ( ccfbuf != NULL ) free( ccfbuf );

  return E_NONE;

}


extern Status WindowCcfWgt
              (const WindowFourier *win,
               const Cmplx *refaddr,
               const Real *refwgt,
               const Cmplx *fouaddr,
               Real *fouwgt,
               Status (*wgtfn)(const void *, Size, Real *),
               void *wgtdat,
               Cmplx *ccfaddr,
               const MaskParam *ccfflt,
               Real *coraddr)

{
  Status status;

  if ( argcheck( win     == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( refaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( fouaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( fouwgt  == NULL ) ) return exception( E_ARGVAL );

  Size fousize = win->fousize;

  if ( wgtfn != NULL ) {
    if ( runcheck && ( fouwgt ==  NULL ) ) return exception( E_WINDOWFOURIER ); 
    status = wgtfn( wgtdat, fousize, fouwgt );
    if ( exception( status ) ) return status;
    if ( refwgt != NULL ) {
      for ( Size i = 0; i < fousize; i++ ) {
        fouwgt[i] *= refwgt[i];
      }
    }
    refwgt = fouwgt;
  }
  if ( refwgt != NULL ) {
    Real *f = (Real *)fouaddr;
    for ( Size i = 0; i < fousize; i++ ) {
      *f++ *= refwgt[i];
      *f++ *= refwgt[i];
    }
  }

  status = WindowCcf( win, refaddr, fouaddr, ccfaddr, ccfflt, coraddr );
  if ( exception( status ) ) return status;

  return E_NONE;

}
