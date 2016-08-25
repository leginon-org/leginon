/*----------------------------------------------------------------------------*
*
*  windowcut.c  -  window: image window processing
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
#include "transfer.h"
#include "exception.h"
#include <string.h>


/* types */

typedef struct {
  Type srctype;
  const void *srcaddr;
  Real *dstaddr;
  TransferParam *transfer;
} WindowCutData;


/* functions */

static Status WindowCutSrc
              (Offset offs,
               Size count,
               Size elsize,
               void *buf,
               void *data)

{
  WindowCutData *cut = data;
  const char *addr = cut->srcaddr;

  memcpy( buf, addr + offs, count * elsize );

  return E_NONE;

}


static Status WindowCutCpy
              (Size len,
               Size srcelsize,
               const void *srcbuf,
               Size dstelsize,
               void *dstbuf,
               void *data)

{
  WindowCutData *cut = data;
  Status status;

  status = ScaleReal( cut->srctype, len, srcbuf, dstbuf, cut->transfer );
  if ( exception( status ) ) return status;

  return E_NONE;

}


static Status WindowCutDst
              (Offset offs,
               Size count,
               Size elsize,
               const void *buf,
               void *data)

{
  WindowCutData *cut = data;
  Real *addr = cut->dstaddr + offs / elsize;

  memcpy( addr, buf, count * elsize );

  return E_NONE;

}


extern Status WindowCut
              (const Size *len,
               Type type,
               const void *addr,
               const Size *ori,
               const Window *win,
               Real *winaddr,
               Size *count,
               const MaskParam *winmsk)

{
  Status area = E_NONE;
  Status status;

  if ( argcheck( len  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( win  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( winaddr == NULL ) ) return exception( E_ARGVAL );

  /* clipped window */
  Size cutlen[win->dim], cutsize;
  status = ArrayBox( win->dim, len, ori, win->len, cutlen, &cutsize );
  if ( count != NULL ) *count = cutsize;
  if ( ( win->area <= 1 ) && ( cutsize < win->area * win->size ) ) {
    area = E_WINDOW_AREA;
  }

  /* cut */
  WindowCutData data = { type, addr, winaddr, NULL };
  status = ArrayFnCutPaste( win->dim, len, ori, cutlen, NULL, win->len, TypeGetSize( type ), sizeof(Real), WindowCutSrc, WindowCutCpy, WindowCutDst, &data );
  if ( exception( status ) ) return status;

  /* image mask */
  if ( winmsk != NULL ) {
    status = MaskReal( win->dim, win->len, winaddr, NULL, NULL, winmsk );
    if ( exception( status ) ) return status;
  }

  return area;

}


extern Status WindowCutNorm
              (const Size *len,
               Type type,
               const void *addr,
               const Size *ori,
               const Window *win,
               Real *winaddr,
               Size *count,
               const MaskParam *winmsk)

{
  Stat stat;
  Status area = E_NONE;
  Status status;

  if ( argcheck( len  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( win  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( winaddr == NULL ) ) return exception( E_ARGVAL );

  /* clipped window */
  Size cutlen[win->dim], cutsize;
  status = ArrayBox( win->dim, len, ori, win->len, cutlen, &cutsize );
  if ( count != NULL ) *count = cutsize;
  if ( ( win->area <= 1 ) && ( cutsize < win->area * win->size ) ) {
    area = E_WINDOW_AREA;
  }

  /*  compute statistics */
  WindowCutData data = { type, addr, winaddr, NULL };
  status = ArrayFnCut( win->dim, len, ori, cutlen, TypeGetSize( type ), sizeof(Real), WindowCutSrc, WindowCutCpy, WindowCutDst, &data );
  if ( exception( status ) ) return status;
  StatParam statparam = StatParamInitializer;
  statparam.flags = StatMean | StatSd;
  status = MinmaxmeanReal( cutsize, winaddr, &stat, &statparam );
  if ( exception( status ) ) return status;

  /* cut */
  TransferParam transfer = TransferParamInitializer;
  transfer.bias = stat.mean;
  transfer.flags = TransferBias;
  if ( stat.sd > 0 ) {
    transfer.scale = 1.0 / stat.sd;
    transfer.flags |= TransferScale;
  }
  data.transfer = &transfer;
  status = ArrayFnCutPaste( win->dim, len, ori, cutlen, NULL, win->len, TypeGetSize( type ), sizeof(Real), WindowCutSrc, WindowCutCpy, WindowCutDst, &data );
  if ( exception( status ) ) return status;

  /* image mask */
  if ( winmsk != NULL ) {
    status = MaskReal( win->dim, win->len, winaddr, NULL, NULL, winmsk );
    if ( exception( status ) ) return status;
  }

  return area;

}
