/*----------------------------------------------------------------------------*
*
*  heapmem.c  -  io: heap procedures
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
#include "heapdebug.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Heap *HeapMemCreate
             (const HeapParam *param)

{
  Status status;

  HeapData *data = malloc( sizeof(HeapData) );
  if ( data == NULL ) return NULL;
  *data = HeapDataInitializer;

  HeapParam hpar = ( param == NULL ) ? HeapParamInitializer : *param;
  hpar.mode |= IONew | IORd;

  HeapDebugProc( "mem.create", "mode", hpar.mode );

  Heap *heap = HeapInit( HeapProcMem, data, &hpar );
  status = testcondition( heap == NULL );
  if ( status ) return NULL; /* data freed in HeapInit */

  return heap;

}


extern Status HeapMemDestroy
              (Heap *heap)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  status = HeapFinal( heap, E_NONE );
  logexception( status );

  HeapDebugProc( "mem.destroy", "stat", status );

  return status;

}
