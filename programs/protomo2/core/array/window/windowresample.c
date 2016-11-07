/*----------------------------------------------------------------------------*
*
*  windowresample.c  -  window: image window processing
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
#include "linear.h"
#include "exception.h"


/* functions */

extern Status WindowResample
              (const Size *len,
               Type type,
               const void *addr,
               const Coord *A,
               const Coord *b,
               const Window *win,
               Real *winaddr,
               Stat *winstat,
               const MaskParam *winmsk)

{
  Status area = E_NONE;
  Status status;

  if ( argcheck( len  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( win  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( winaddr == NULL ) ) return exception( E_ARGVAL );

  /* resample and compute statistics */
  Stat stat = StatInitializer;
  TransformParam transform = TransformParamInitializer;
  transform.stat = &stat;
  status = LinearReal( win->dim, type, len, addr, A, b, win->len, winaddr, NULL, &transform );
  if ( status && ( status != E_TRANSFORM_CLIP ) ) return exception( status );
  if ( ( win->area <= 1 ) && ( stat.count < win->area * win->size ) ) {
    area = E_WINDOW_AREA;
  }

  if ( winstat != NULL ) {

    /* resample and subtract mean value, normalize to std dev, fill out of bounds areas with zeroes (new mean value) */
    TransferParam transfer;
    transfer.bias = stat.mean;
    transfer.flags = TransferBias;
    if ( stat.sd > 0 ) {
      transfer.scale = 1.0 / stat.sd;
      transfer.flags |= TransferScale;
    }
    transform.stat = winstat;
    transform.transf = &transfer;
    transform.fill = 0;
    transform.flags = TransformFill;
    status = LinearReal( win->dim, type, len, addr, A, b, win->len, winaddr, NULL, &transform );
    if ( status && ( status != E_TRANSFORM_CLIP ) ) return exception( status );

  }

  /* image mask */
  if ( winmsk != NULL ) {
    status = MaskReal( win->dim, win->len, winaddr, NULL, NULL, winmsk );
    if ( exception( status ) ) return status;
  }

  return area;

}
