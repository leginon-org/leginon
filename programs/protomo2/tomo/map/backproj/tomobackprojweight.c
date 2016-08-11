/*----------------------------------------------------------------------------*
*
*  tomobackprojweight.c  -  map: weighted backprojection
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomobackproj.h"
#include "tomomapcommon.h"
#include "fourier.h"
#include "thread.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>


/* functions */

static Status TomobackprojWeightExec
              (Size thread,
               const void *inarg,
               void *outarg)

{
  const Tomomap *map = inarg;
  Real *H = outarg;
  Status status;

  if ( map->flags & TomoMsg ) {
    MessageFormat( "weighting projection %"SizeU"\n", thread );
  }

  Tomoproj *proj = map->proj + thread;
  Size len[2]; Index low[2];

  len[0] = proj->len[0] / 2 + 1;
  len[1] = proj->len[1];

  low[0] = 0;
  low[1] = -(Index)( proj->len[1] / 2 );

  Size fousize = len[0] * len[1];
  Cmplx *fouaddr = malloc( fousize * sizeof(*fouaddr) );
  if ( fouaddr == NULL ) return exception( E_MALLOC );

  status = FourierReal( 2, proj->len, proj->img, fouaddr, 1, FourierZeromean );
  if ( pushexception( status ) ) goto exit;

  if ( outarg == NULL ) {

    Tomotransfer *trans = map->data.trans + thread;

    H = malloc( fousize * sizeof(*H) );
    if ( H == NULL ) { status = exception( E_MALLOC ); goto exit;}

    Coord A[3][3];
    TomotransferScale( trans->A, map->sampling, proj->len, A );

    TomotransferParam param;
    param.body = map->mode.param.bck.body * map->sampling;
    param.bwid = map->mode.param.bck.bwid;
    param.bfsh = ( map->mode.type == TomomapBpr ) ? TomotransferFsh( trans->A ) : 1;

    TomotransferCalc( len, low, map->data.trans, map->count, A, H, &param );

  }

  Coord thr2 = map->mode.param.bck.bthr; thr2 *= thr2;
  Real *addr = (Real *)fouaddr;

  for ( Size k = 0; k < fousize; k++ ) {
    /* thresholded transfer function */
    Coord h = H[k];
    h = Sqrt( h * h + thr2 );
    if ( H[k] < 0 ) h = -h;
    /* weighting */
    Real w = 1 / h;
    *addr++ *= w;
    *addr++ *= w;
  }

  if ( outarg == NULL ) free( H );

  if ( map->diam[0] > 0 ) {
    Coord b[2] = { -low[0], -low[1] };
    Cmplx v; Cset( v, 0, 0 );
    MaskFlags flags = MaskModeFract | MaskModeSym;
    if ( proj->len[0] % 2 ) flags |= MaskModeNodd;
    status = MaskEllipsApod2dCmplx( len, fouaddr, NULL, b, map->diam, map->apod, v, flags );
    if ( pushexception( status ) ) goto exit;
  }

  status = FourierInvReal( 2, proj->len, fouaddr, proj->img, 1, FourierZeromean );
  if ( pushexception( status ) ) goto exit;

  exit:

  free( fouaddr );

  return status;

}


extern Status TomobackprojWeight
              (Tomomap *map,
               Real **transfer)

{
  Status status;

  Thread *thread = malloc( map->count * sizeof(Thread) );
  if ( thread == NULL ) return exception( E_MALLOC );

  for ( Size t = 0; t < map->count; t++ ) {
    thread[t].function = TomobackprojWeightExec;
    thread[t].inarg = map;
    thread[t].outarg = ( transfer == NULL ) ? NULL : transfer[t];
  }

  if ( map->flags & TomoMsg ) {
    MessageFormat( "%"SizeU" projections\n", map->count );
  }

  status = ThreadExec( map->count, thread );
  if ( status == E_THREAD_ERROR ) {
    logexception( status );
  } else if ( status ) {
    pushexception( status );
  }

  free( thread );

  return status;

}
