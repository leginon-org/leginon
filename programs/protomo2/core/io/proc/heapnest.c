/*----------------------------------------------------------------------------*
*
*  heapnest.c  -  io: heap procedures
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "heapproccommon.h"
#include "heapcommon.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Heap *HeapNestInit
             (Heap *heap,
              int segm,
              HeapMeta meta,
              const HeapParam *param)

{
  Status status;

  if ( argcheck( heap == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( segm < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }

  HeapParam hpar = ( param == NULL ) ? HeapParamInitializer : *param;

  HeapData *data = malloc( sizeof(HeapData) );
  if ( data == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *data = HeapDataInitializer;

  if ( hpar.mode & ( IONew | IOCre ) ) {

    if ( ~hpar.mode & IONew ) {
      status = HeapAccess( heap, segm, NULL, NULL, NULL );
      if ( !status ) {
        status = HeapDealloc( heap, segm );
        if ( pushexception( status ) ) goto error;
      }
    }

    status = HeapAlloc( heap, segm, 0, meta, &data->offs );
    if ( pushexception( status ) ) goto error;

    data->size = 0;

  } else {

    status = HeapAccess( heap, segm, &data->offs, &data->size, &meta );
    if ( pushexception( status ) ) goto error;

  }

  if ( ( data->offs < 0 ) || ( data->size < 0 ) ) {
    status = pushexception( E_HEAPPROC ); goto error;
  }

  hpar.mode &= heap->mode & ( IORd | IOWr | IOMod | IOExt );
  hpar.mode |= heap->mode & ( IOOld | IONew | IOCre | IOShr | IOXcl | IOLck | IOBuf );

  data->handle = heap;
  data->segm = segm;
  data->mode = hpar.mode;

  Heap *nest = HeapInit( HeapProcNest, data, &hpar );
  status = testcondition( nest == NULL );
  if ( status ) return NULL; /* data freed in HeapInit */

  nest->stat |= HeapStatNest;

  heap->nestcount++;

  return nest;

  error: free( data );

  return NULL;

}
