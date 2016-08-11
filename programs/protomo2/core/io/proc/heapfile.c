/*----------------------------------------------------------------------------*
*
*  heapfile.c  -  io: heap procedures
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
#include "macros.h"
#include <stdlib.h>


/* functions */

extern Heap *HeapFileInit
             (Fileio *fileio,
              const HeapFileParam *param)

{
  const HeapProc *hproc;
  Bool map, std;
  Status status;

  if ( argcheck( fileio == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  status = FileioStatusMap( fileio, &map );
  if ( pushexception( status ) ) return NULL;

  status = FileioStatusStd( fileio, &std );
  if ( pushexception( status ) ) return NULL;

  const HeapFileProc *proc = ( param == NULL ) ? NULL : param->proc;
  const HeapFileProc *defaultproc = ( param == NULL ) ? NULL : param->defaultproc;

  if ( map ) {
    hproc = ( ( proc == NULL ) || ( proc->mmap == NULL ) ) ? HeapProcGetMmap( defaultproc ) : proc->mmap;
  } else if ( std ) {
    hproc = ( ( proc == NULL ) || ( proc->std == NULL ) ) ? HeapProcGetStd( defaultproc ) : proc->std;
  } else {
    hproc = ( ( proc == NULL ) || ( proc->sys == NULL ) ) ? HeapProcGetSys( defaultproc ) : proc->sys;
  }

  HeapParam hpar = HeapParamInitializer;
  if ( ( param != NULL ) && ( param->param != NULL ) ) hpar = *param->param;

  HeapData *data = malloc( sizeof(HeapData) );
  if ( data == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *data = HeapDataInitializer;

  data->handle = fileio;
  if ( param != NULL ) {
    data->offs = param->offs;
    data->size = MIN( param->size, OffsetMaxSize );
    data->mode = hpar.mode;
  }

  Heap *heap = HeapInit( hproc, data, &hpar );
  status = testcondition( heap == NULL );
  if ( status ) return NULL; /* data freed in HeapInit */

  return heap;

}



extern Status HeapFileResizeSub
              (HeapData *data,
               Offset *oldsize,
               Offset newsize)

{
  Status status;

  if ( newsize < 1 ) newsize = 1;

  Offset size = newsize;
  if ( data->offs > 0 ) {
    if ( OFFSETADDOVFL( size, data->offs ) ) return exception( E_INTOVFL );
    size += data->offs;
  }

  if ( newsize > *oldsize ) {

    status = FileioAllocate( data->handle, size );
    if ( exception( status ) ) return status;

  } else {

    status = FileioTruncate( data->handle, size );
    if ( exception( status ) ) return status;

  }

  *oldsize = newsize;

  return E_NONE;

}


extern Status HeapFileResize
              (void *heapdata,
               Offset *oldsize,
               Offset newsize)

{
  HeapData *data = heapdata;
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( newsize < 0  ) ) return exception( E_ARGVAL );

  if ( runcheck && ( data->handle == NULL ) ) return exception( E_HEAPPROC );

  if ( data->size > 0 ) return exception( E_HEAPPROC );

  if ( newsize == *oldsize ) return E_NONE;

  status = HeapFileResizeSub( data, oldsize, newsize );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status HeapFileSync
              (void *heapdata)

{
  HeapData *data = heapdata;
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && ( data->handle == NULL ) ) return exception( E_HEAPPROC );

  status = FileioFlush( data->handle );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status HeapFileFinal
              (void *heapdata,
               Status fail)

{
  HeapData *data = heapdata;
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && ( data->handle == NULL ) ) return exception( E_HEAPPROC );

  if ( ~data->mode & IOFd ) {

    if ( !fail ) {
      status = FileioClearMode( data->handle, IODel );
      logexception( status );
    } else if ( fail == E_HEAPPROC_DEL ) {
      status = FileioSetMode( data->handle, IODel );
      logexception( status );
    }

    status = FileioClose( data->handle );
    logexception( status );

  }

  free( data );

  return E_NONE;

}
