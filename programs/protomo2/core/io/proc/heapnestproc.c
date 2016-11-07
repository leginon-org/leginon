/*----------------------------------------------------------------------------*
*
*  heapnestproc.c  -  io: heap procedures
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

static Status HeapNestAddr
              (void *heapdata,
               Offset offset,
               Size size,
               void **buf)

{
  HeapData *data = heapdata;
  void *addr;
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( offset < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( offset > OffsetMaxSize ) ) return exception( E_ARGVAL );

  Heap *heap = data->handle;
  if ( runcheck && ( heap == NULL ) ) return exception( E_HEAPPROC );

  if ( size > (Size)OffsetMaxSize ) return exception( E_HEAPPROC_OFF );

  if ( OFFSETADDOVFL( offset, (Offset)size ) ) return exception( E_HEAPPROC_OFF );
  Offset end = offset + size;

  if ( end > data->size ) return exception( E_HEAPPROC_OFF );

  if ( OFFSETADDOVFL( offset, data->offs ) ) return exception( E_HEAPPROC_OFF );
  offset += data->offs;

  if ( heap->proc->addr == NULL ) return exception( E_HEAPPROC );
  status = heap->proc->addr( heap->data, offset, size, &addr );
  if ( exception( status ) ) return status;

  *buf = addr;

  return E_NONE;

}


static Status HeapNestRead
              (void *heapdata,
               Offset offset,
               Size size,
               void *buf)

{
  HeapData *data = heapdata;
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( offset < 0 ) ) return exception( E_ARGVAL );

  Heap *heap = data->handle;
  if ( runcheck && ( heap == NULL ) ) return exception( E_HEAPPROC );

  if ( size > (Size)OffsetMaxSize ) return exception( E_HEAPPROC_OFF );

  if ( size ) {

    if ( OFFSETADDOVFL( offset, (Offset)size ) ) return exception( E_HEAPPROC_OFF );
    Offset end = offset + size;

    if ( end > data->size ) return exception( E_HEAPPROC_OFF );

    if ( OFFSETADDOVFL( offset, data->offs ) ) return exception( E_HEAPPROC_OFF );
    offset += data->offs;

    if ( heap->proc->read == NULL ) return exception( E_HEAPPROC );
    status = heap->proc->read( heap->data, offset, size, buf );
    if ( exception( status ) ) return status;

  }

  return E_NONE;

}


static Status HeapNestWrite
              (void *heapdata,
               Offset offset,
               Size size,
               const void *buf)

{
  HeapData *data = heapdata;
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( offset < 0 ) ) return exception( E_ARGVAL );

  Heap *heap = data->handle;
  if ( runcheck && ( heap == NULL ) ) return exception( E_HEAPPROC );

  if ( size > (Size)OffsetMaxSize ) return exception( E_HEAPPROC_OFF );

  if ( size ) {

    if ( OFFSETADDOVFL( offset, (Offset)size ) ) return exception( E_HEAPPROC_OFF );
    Offset end = offset + size;

    if ( end > data->offs ) return exception( E_HEAPPROC_OFF );

    if ( OFFSETADDOVFL( offset, data->offs ) ) return exception( E_HEAPPROC_OFF );
    offset += data->offs;

    if ( heap->proc->write == NULL ) return exception( E_HEAPPROC );
    status = heap->proc->write( heap->data, offset, size, buf );
    if ( exception( status ) ) return status;

  }

  return E_NONE;

}


static Status HeapNestResize
              (void *heapdata,
               Offset *oldsize,
               Offset newsize)

{
  HeapData *data = heapdata;
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( newsize < 0  ) ) return exception( E_ARGVAL );

  Heap *heap = data->handle;
  if ( runcheck && ( heap == NULL ) ) return exception( E_HEAPPROC );

  if ( newsize == *oldsize ) return E_NONE;

  status = HeapResize( heap, data->segm, newsize, &data->offs );
  if ( exception( status ) ) return status;

  data->size = newsize;

  *oldsize = newsize;

  return E_NONE;

}


static Status HeapNestSync
              (void *heapdata)

{
  HeapData *data = heapdata;
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );

  Heap *heap = data->handle;
  if ( runcheck && ( heap == NULL ) ) return exception( E_HEAPPROC );

  status = HeapFlush( heap );
  if ( exception( status ) ) return status;

  return E_NONE;

}


static Status HeapNestFinal
              (void *heapdata,
               Status fail)

{
  HeapData *data = heapdata;
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );

  Heap *heap = data->handle;
  if ( runcheck && ( heap == NULL ) ) return exception( E_HEAPPROC );

  if ( fail && ( data->mode & ( IONew | IOCre ) ) ) {
    status = HeapDealloc( heap, data->segm );
    logexception( status );
  }

  free( data );

  if ( !heap->nestcount ) return exception( E_HEAPPROC );
  heap->nestcount--;

  return E_NONE;

}


/* variables */

static const HeapProc HeapProcNestStruct = {
  NULL,
  HeapNestAddr,
  HeapNestRead,
  HeapNestWrite,
  HeapNestResize,
  NULL,
  NULL,
  HeapNestSync,
  HeapNestFinal,
};

const HeapProc *HeapProcNest = &HeapProcNestStruct;
