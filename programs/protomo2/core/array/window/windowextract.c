/*----------------------------------------------------------------------------*
*
*  windowextract.c  -  window: image window processing
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
} WindowExtractData;


/* functions */

static Status WindowExtractSrc
              (Offset offs,
               Size count,
               Size elsize,
               void *buf,
               void *data)

{
  WindowExtractData *extr = data;
  const char *addr = extr->srcaddr;

  memcpy( buf, addr + offs, count * elsize );

  return E_NONE;

}


static Status WindowExtractCpy
              (Size len,
               Size srcelsize,
               const void *srcbuf,
               Size dstelsize,
               void *dstbuf,
               void *data)

{
  WindowExtractData *extr = data;
  Status status;

  status = ScaleReal( extr->srctype, len, srcbuf, dstbuf, extr->transfer );
  if ( exception( status ) ) return status;

  return E_NONE;

}


static Status WindowExtractDst
              (Offset offs,
               Size count,
               Size elsize,
               const void *buf,
               void *data)

{
  WindowExtractData *extr = data;
  Real *addr = extr->dstaddr + offs / elsize;

  memcpy( addr, buf, count * elsize );

  return E_NONE;

}


extern Status WindowExtract
              (const Size *len,
               Type type,
               const void *addr,
               const Size *b,
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
  Size extori[win->dim], extpos[win->dim], extlen[win->dim], extsize;
  status = ArrayBoxCtr( win->dim, len, b, win->len, extori, extpos, extlen, &extsize );
  if ( count != NULL ) *count = extsize;
  if ( ( win->area <= 1 ) && ( extsize < win->area * win->size ) ) {
    area = E_WINDOW_AREA;
  }

  /* extract */
  WindowExtractData data = { type, addr, winaddr, NULL };
  status = ArrayFnCutPaste( win->dim, len, extori, extlen, extpos, win->len, TypeGetSize( type ), sizeof(Real), WindowExtractSrc, WindowExtractCpy, WindowExtractDst, &data );
  if ( exception( status ) ) return status;

  /* image mask */
  if ( winmsk != NULL ) {
    status = MaskReal( win->dim, win->len, winaddr, NULL, NULL, winmsk );
    if ( exception( status ) ) return status;
  }

  return area;

}


extern Status WindowExtractNorm
              (const Size *len,
               Type type,
               const void *addr,
               const Size *b,
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
  Size extori[win->dim], extpos[win->dim], extlen[win->dim], extsize;
  status = ArrayBoxCtr( win->dim, len, b, win->len, extori, extpos, extlen, &extsize );
  if ( count != NULL ) *count = extsize;
  if ( ( win->area <= 1 ) && ( extsize < win->area * win->size ) ) {
    area = E_WINDOW_AREA;
  }

  /*  compute statistics */
  WindowExtractData data = { type, addr, winaddr, NULL };
  status = ArrayFnCut( win->dim, len, extori, extlen, TypeGetSize( type ), sizeof(Real), WindowExtractSrc, WindowExtractCpy, WindowExtractDst, &data );
  if ( exception( status ) ) return status;
  StatParam statparam = StatParamInitializer;
  statparam.flags = StatMean | StatSd;
  status = MinmaxmeanReal( extsize, winaddr, &stat, &statparam );
  if ( exception( status ) ) return status;

  /* extract */
  TransferParam transfer = TransferParamInitializer;
  transfer.bias = stat.mean;
  transfer.flags = TransferBias;
  if ( stat.sd > 0 ) {
    transfer.scale = 1.0 / stat.sd;
    transfer.flags |= TransferScale;
  }
  data.transfer = &transfer;
  status = ArrayFnCutPaste( win->dim, len, extori, extlen, extpos, win->len, TypeGetSize( type ), sizeof(Real), WindowExtractSrc, WindowExtractCpy, WindowExtractDst, &data );
  if ( exception( status ) ) return status;

  /* image mask */
  if ( winmsk != NULL ) {
    status = MaskReal( win->dim, win->len, winaddr, NULL, NULL, winmsk );
    if ( exception( status ) ) return status;
  }

  return area;

}
