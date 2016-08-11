/*----------------------------------------------------------------------------*
*
*  windowtransform.c  -  window: image windows processing
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
#include "imagearray.h"
#include "imagemask.h"
#include "exception.h"


/* functions */

extern Status WindowFourierPower
              (const WindowFourier *win,
               const Cmplx *fouaddr,
               Real *foupwr)


{
  Status status;

  if ( argcheck( win     == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( fouaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( foupwr  == NULL ) ) return exception( E_ARGVAL );

  status = ImageSumAbs2( &win->fou, fouaddr, foupwr );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status WindowTransform
              (const WindowFourier *win,
               const Real *imgaddr,
               Cmplx *fouaddr,
               Real *foupwr,
               const MaskParam *fouflt)


{
  Status status;

  if ( argcheck( win     == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( imgaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( fouaddr == NULL ) ) return exception( E_ARGVAL );

  status = FourierRealTransf( win->forw, imgaddr, fouaddr, 1 );
  if ( exception( status ) ) return status;

  status = CCFmodCmplx( win->fousize, fouaddr, win->mode );
  if ( exception( status ) ) return status;

  if ( fouflt != NULL ) {
    status = ImageMask( &win->fou, fouaddr, NULL, NULL, fouflt );
    if ( exception( status ) ) return status;
  }

  if ( foupwr != NULL ) {
    status = ImageSumAbs2( &win->fou, fouaddr, foupwr );
    if ( exception( status ) ) return status;
  }

  return E_NONE;

}


extern Status WindowTransformTrf
              (const WindowFourier *win,
               const Real *imgaddr,
               const Coord *A,
               Cmplx *fouaddr,
               Real *foupwr,
               const MaskParam *fouflt)


{
  Status status;

  if ( argcheck( win     == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( imgaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( fouaddr == NULL ) ) return exception( E_ARGVAL );

  status = FourierRealTransf( win->forw, imgaddr, fouaddr, 1 );
  if ( exception( status ) ) return status;

  status = CCFmodCmplx( win->fousize, fouaddr, win->mode );
  if ( exception( status ) ) return status;

  if ( fouflt != NULL ) {
    status = ImageMask( &win->fou, fouaddr, A, NULL, fouflt );
    if ( exception( status ) ) return status;
  }

  if ( foupwr != NULL ) {
    status = ImageSumAbs2( &win->fou, fouaddr, foupwr );
    if ( exception( status ) ) return status;
  }

  return E_NONE;

}
