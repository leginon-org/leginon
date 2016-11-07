/*----------------------------------------------------------------------------*
*
*  tomobackprojtransfer.c  -  map: weighted backprojection
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
#include "thread.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

static Status TomobackprojTransferExec
              (Size thread,
               const void *inarg,
               void *outarg)

{
  const Tomomap *map = inarg;
  Real **H = outarg;

  Tomoproj *proj = map->proj + thread;
  Size len[2]; Index low[2];

  len[0] = proj->len[0] / 2 + 1;
  len[1] = proj->len[1];

  low[0] = 0;
  low[1] = -(Index)( proj->len[1] / 2);

  Size fousize = len[0] * len[1];
  *H = malloc( fousize * sizeof(*H) );
  if ( *H == NULL ) return pushexception( E_MALLOC );

  Tomotransfer *trans = map->data.trans + thread;

  Coord A[3][3];
  TomotransferScale( trans->A, map->sampling, proj->len, A );

  TomotransferParam param;
  param.body = map->mode.param.bck.body * map->sampling;
  param.bwid = map->mode.param.bck.bwid;
  param.bfsh = ( map->mode.type == TomomapBpr ) ? TomotransferFsh( trans->A ) : 1;

  TomotransferCalc( len, low, map->data.trans, map->count, A, *H, &param );

  return E_NONE;

}


extern Status TomobackprojTransfer
              (Tomomap *map,
               Real **transfer)

{
  Status status;

  Thread *thread = malloc( map->count * sizeof(Thread) );
  if ( thread == NULL ) return exception( E_MALLOC );

  for ( Size t = 0; t < map->count; t++ ) {
    thread[t].function = TomobackprojTransferExec;
    thread[t].inarg = map;
    thread[t].outarg = transfer + t;
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
