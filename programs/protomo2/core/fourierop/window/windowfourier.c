/*----------------------------------------------------------------------------*
*
*  windowfourier.c  -  window: image windows
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
#include <stdlib.h>
#include <string.h>


/* variables */

static Coord WindowMaskDefaultWid[] = { 0.90, 0.90, 0.90 };
static Coord WindowMaskDefaultApo[] = { 0.03, 0.03, 0.03 };

#define DefaultMaskFlags ( MaskFunctionEllips | MaskModeApod | MaskModeUnit | MaskModeFract )

static MaskParam WindowMaskDefault[] = {
  {  NULL, NULL, WindowMaskDefaultWid, WindowMaskDefaultApo, 0.0, DefaultMaskFlags },
  {  NULL, NULL, NULL,                 NULL,                 0.0, MaskFunctionNone }
};


static Coord WindowLopassFilterDefaultWid[] = { 0.90, 0.90, 0.90 };
static Coord WindowLopassFilterDefaultApo[] = { 0.03, 0.03, 0.03 };

static Coord WindowHipassFilterDefaultWid[] = { 0.05, 0.05, 0.05 };
static Coord WindowHipassFilterDefaultApo[] = { 0.01, 0.01, 0.01 };

#define DefaultFilterFlags ( MaskFunctionEllips | MaskModeApod | MaskModeUnit | MaskModeFract )

static MaskParam WindowFilterDefault[] = {
  {  NULL, NULL, WindowLopassFilterDefaultWid, WindowLopassFilterDefaultApo, 0.0, DefaultFilterFlags               },
  {  NULL, NULL, WindowHipassFilterDefaultWid, WindowHipassFilterDefaultApo, 0.0, DefaultFilterFlags | MaskModeInv },
  {  NULL, NULL, NULL,                         NULL,                         0.0, MaskFunctionNone                 }
};


/* functions */

extern Status WindowFourierInit
              (Size dim,
               const Size *len,
               const MaskParam *msk,
               const MaskParam *flt,
               const PeakParam *pkpar,
               WindowFourier *win,
               const WindowFourierParam *param)

{
  Status status;

  if ( argcheck( dim == 0    ) ) return exception( E_ARGVAL );
  if ( argcheck( len == NULL ) ) return exception( E_ARGVAL );

  WindowFourierParam par = ( param == NULL ) ? WindowFourierParamInitializer : *param;

  Image img;
  img.dim = dim;
  img.len = malloc( dim * sizeof(Size) );
  img.low = NULL;
  img.type = TypeReal;
  img.attr = ImageRealspc;
  if ( img.len == NULL ) return exception( E_MALLOC );
  memcpy( img.len, len, dim * sizeof(Size) );

  Image fou;
  status = ImageMetaCopyAlloc( &img, &fou, ImageModeFou );
  if ( exception( status ) ) goto error1;

  Size fousize;
  status = ArraySize( dim, fou.len, sizeof(Cmplx), &fousize );
  if ( exception( status ) ) return status;
  if ( !fousize ) {
    status = exception( E_ARRAY_ZERO ); goto error2;
  }

  Fourier *forw = NULL, *back = NULL;
  if ( par.forw ) {
    forw = FourierRealInit( dim, len, par.opt );
    status = popcondition( forw == NULL );
    if ( status ) goto error2;
  }
  if ( par.back ) {
    back = FourierInvRealInit( dim, len, par.opt );
    status = popcondition( back == NULL );
    if ( status ) goto error3;
  }

  if ( msk != NULL ) {
    if ( !( msk->flags & MaskFunctionMask ) ) msk = NULL;
  }
  if ( msk == NULL ) {
    if ( param->mskdefault ) msk = WindowMaskDefault;
  }

  if ( flt != NULL ) {
    if ( !( flt->flags & MaskFunctionMask ) ) flt = NULL;
  }
  if ( flt == NULL ) {
    if ( param->fltdefault ) flt = WindowFilterDefault;
  }

  win->img = img;
  win->fou = fou;
  win->fousize = fousize;
  win->forw = forw;
  win->back = back;
  win->mode = par.mode;
  win->msk = msk;
  win->flt = flt;
  win->pkpar = pkpar;

  return E_NONE;

  error3: if ( forw != NULL ) exception( FourierFinal( forw ) );
  error2: free( fou.len );
  error1: free( img.len );

  return status;

}


extern Status WindowFourierFinal
              (WindowFourier *win)

{
  Status stat, status = E_NONE;

  if ( win->back != NULL ) {
    stat = FourierFinal( win->back );
    if ( exception( stat ) ) status = stat;
  }

  if ( win->forw != NULL ) {
    stat = FourierFinal( win->forw );
    if ( exception( stat ) ) status = stat;
  }

  free( win->fou.len );
  free( win->fou.low );

  free( win->img.len );

  return status;

}
