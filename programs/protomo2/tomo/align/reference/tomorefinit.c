/*----------------------------------------------------------------------------*
*
*  tomorefinit.c  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoref.h"
#include "mat3.h"
#include "baselib.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomorefInit
              (Tomoref *ref,
               Tomoimage *image,
               const Window *window,
               const WindowFourier *fourier,
               const TomorefParam *param)

{
  Status status = E_NONE;

  if ( argcheck( ref == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( image == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( window == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( fourier == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( param == NULL ) ) return pushexception( E_ARGVAL );

  ref->image = image;
  ref->window = window;
  ref->fourier = fourier;
  ref->mode = param->mode;
  ref->transcount = 0;
  ref->mincount = 0;
  ref->maxcount = 0;
  ref->excl = SizeMax;
  ref->flags |= param->flags & ( TomoflagMask | TomoflagMaskWrt );

  if ( ref->flags & TomoDryrun ) {
    ref->flags &= ~TomoflagMaskWrt;
  }

  const Tomoseries *series = ref->series;
  const TomotiltImage *tiltimage = series->tilt->tiltimage;
  TomoimageList *list = image->list;

  for ( Size index = 0; index < series->tilt->images; index++, list++, tiltimage++ ) {
    list->flags &= ~TomoimageRef;
    if ( list->flags & TomoimageSel ) {
      if ( SelectExclude( param->selection, param->exclusion, tiltimage->number ) ) list->flags |= TomoimageRef;
    }
  }

  image->list[image->cooref].flags |= TomoimageRef;

  return status;

}


extern Status TomorefFinal
              (Tomoref *ref)

{
  Status status = E_NONE;

  if ( argcheck( ref == NULL ) ) return pushexception( E_ARGVAL );

  if ( ref->trans != NULL ) {
    free( ref->trans ); ref->trans = NULL;
  }

  return status;

}
