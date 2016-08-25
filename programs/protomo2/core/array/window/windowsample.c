/*----------------------------------------------------------------------------*
*
*  windowsample.c  -  window: image window processing
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
#include "sample.h"
#include "transfer.h"
#include "exception.h"


/* functions */

extern Status WindowSample
              (const Size *len,
               Type type,
               const void *addr,
               const Size *smp,
               const Size *b,
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

  /* sample and compute statistics */
  Stat stat = StatInitializer;
  SampleParam sample = SampleParamInitializer;
  sample.stat = &stat;
  sample.flags = SampleConvol | SampleClip;
  status = SampleReal( win->dim, type, len, addr, smp, b, win->len, winaddr, NULL, &sample );
  if ( status && ( status != E_SAMPLE_CLIP ) ) return exception( status );
  if ( ( win->area <= 1 ) && ( stat.count < win->area * win->size ) ) {
    area = E_WINDOW_AREA;
  }

  if ( winstat != NULL ) {

    /* sample and subtract mean value, normalize to std dev, fill out of bounds areas with zeroes (new mean value) */
    TransferParam transfer;
    transfer.bias = stat.mean;
    transfer.flags = TransferBias;
    if ( stat.sd > 0 ) {
      transfer.scale = 1.0 / stat.sd;
      transfer.flags |= TransferScale;
    }
    sample.stat = winstat;
    sample.transf = &transfer;
    sample.fill = 0;
    sample.flags = SampleFill;
    status = SampleReal( win->dim, type, len, addr, smp, b, win->len, winaddr, NULL, &sample );
    if ( status && ( status != E_SAMPLE_CLIP ) ) return exception( status );

  }

  /* image mask */
  if ( winmsk != NULL ) {
    status = MaskReal( win->dim, win->len, winaddr, NULL, NULL, winmsk );
    if ( exception( status ) ) return status;
  }

  return area;

}
