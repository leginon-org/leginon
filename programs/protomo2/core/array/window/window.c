/*----------------------------------------------------------------------------*
*
*  window.c  -  window: image window
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "window.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status WindowInit
              (Size dim,
               const Size *len,
               Window *win,
               const WindowParam *param)

{
  Size winsize;
  Status status;

  if ( argcheck( !dim ) ) return exception( E_ARGVAL );
  if ( argcheck( len == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( win == NULL ) ) return exception( E_ARGVAL );

  status = ArraySize( dim, len, sizeof(Real), &winsize );
  if ( exception( status ) ) return status;
  if ( !winsize ) return exception( E_ARRAY_ZERO );

  *win = WindowInitializer;

  win->dim = dim;
  win->len = len;
  win->size = winsize;

  if ( param != NULL ) win->area = param->area;
  if ( win->area <= 0 ) win->area = 0.95;

  return E_NONE;

}
