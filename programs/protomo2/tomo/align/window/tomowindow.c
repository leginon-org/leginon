/*----------------------------------------------------------------------------*
*
*  tomowindow.c  -  align: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomowindow.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Tomowindow *TomowindowCreate
                   (const TomowindowParam *param)

{
  Status status;

  if ( param == NULL ) { pushexception( E_ARGVAL ); return NULL; }

  if ( ( param->len == NULL ) || ( param->len[0] < 8 ) || ( param->len[1] < 8 ) ) {
    pushexception( E_TOMOWINDOW_SIZE ); return NULL;
  }

  Tomowindow *window = malloc( sizeof(Tomowindow) );
  if ( window == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *window = TomowindowInitializer;

  WindowParam wpar = WindowParamInitializer;
  wpar.area = param->area;

  status = WindowInit( 2, param->len, &window->img, &wpar );
  if ( pushexception( status ) ) goto error;

  WindowFourierParam fpar = WindowFourierParamInitializer;
  fpar.opt = FourierZeromean;

  status = WindowFourierInit( 2, param->len, param->msk, param->flt, NULL, &window->fou, &fpar );
  if ( pushexception( status ) ) goto error;

  return window;

  /* error handling */

  error: free( window );

  return NULL;

}


extern Status TomowindowCorrInit
              (Tomowindow *window,
               const TomowindowCorrParam *param)

{
  Status status;

  if ( argcheck( window == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( param == NULL ) ) return pushexception( E_ARGVAL );

  WindowParam wpar = WindowParamInitializer;
  wpar.area = param->area;

  status = WindowInit( 2, window->img.len, &window->win, &wpar );
  if ( exception( status ) ) return status;

  window->winmsk = param->msk;
  window->corlen[0] = param->corlen[0];
  window->corlen[1] = param->corlen[1];
  window->cormed = param->cormed;
  window->corflt = param->corflt;

  window->fou.pkpar = param->pk;
  window->fou.mode = param->ccmode;

  return E_NONE;

}


extern Status TomowindowDestroy
              (Tomowindow *window)

{
  Status status;

  if ( argcheck( window == NULL ) ) return pushexception( E_ARGVAL );

  status = WindowFourierFinal( &window->fou );
  pushexception( status );

  free( window );

  return status;

}
