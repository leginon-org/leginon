/*----------------------------------------------------------------------------*
*
*  heapmemproc.c  -  io: heap procedures
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
#include "macros.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status HeapMemInit
              (void *heapdata)

{
  HeapData *data = heapdata;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );

  HeapDebugProc( "mem.init", "size", 0 );

  if ( runcheck && ( data->handle != NULL ) ) return exception( E_HEAPPROC );

  uint8_t *addr = malloc( 1 );
  if ( addr == NULL ) return exception( E_MALLOC );

  data->handle = addr;

  return E_NONE;

}


static Status HeapMemAddr
              (void *heapdata,
               Offset offset,
               Size size,
               void **buf)

{
  HeapData *data = heapdata;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( offset < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( offset > OffsetMaxSize ) ) return exception( E_ARGVAL );

  HeapDebugProc( "mem.addr", "size", size );

  if ( runcheck && ( data->handle == NULL ) ) return exception( E_HEAPPROC );

  uint8_t *addr = data->handle;
  if ( addr == NULL ) return exception( E_HEAPPROC );

  if ( data->size > 0 ) {
    if ( size > (Size)data->size ) return exception( E_HEAPPROC_OFF );
  }

  if ( data->offs > 0 ) {
    if ( OFFSETADDOVFL( offset, data->offs ) ) return exception( E_INTOVFL );
    offset += data->offs;
  }

  if ( offset > OffsetMaxSize ) return exception( E_HEAPPROC_OFF );

  *buf = addr + offset;

  return E_NONE;

}


static Status HeapMemRead
              (void *heapdata,
               Offset offset,
               Size size,
               void *buf)

{
  HeapData *data = heapdata;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( offset < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( offset > OffsetMaxSize ) ) return exception( E_ARGVAL );

  HeapDebugProc( "mem.read", "size", size );

  if ( runcheck && ( data->handle == NULL ) ) return exception( E_HEAPPROC );

  if ( size ) {

    uint8_t *addr = data->handle;
    if ( addr == NULL ) return exception( E_HEAPPROC );

    if ( data->size > 0 ) {
      if ( size > (Size)data->size ) return exception( E_HEAPPROC_OFF );
    }

    if ( data->offs > 0 ) {
      if ( OFFSETADDOVFL( offset, data->offs ) ) return exception( E_INTOVFL );
      offset += data->offs;
    }

    if ( offset > OffsetMaxSize ) return exception( E_HEAPPROC_OFF );

    memcpy( buf, addr + offset, size );

  }

  return E_NONE;

}


static Status HeapMemWrite
              (void *heapdata,
               Offset offset,
               Size size,
               const void *buf)

{
  HeapData *data = heapdata;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( offset < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( offset > OffsetMaxSize ) ) return exception( E_ARGVAL );

  HeapDebugProc( "mem.write", "size", size );

  if ( runcheck && ( data->handle == NULL ) ) return exception( E_HEAPPROC );

  if ( size ) {

    uint8_t *addr = data->handle;
    if ( addr == NULL ) return exception( E_HEAPPROC );

    if ( data->size > 0 ) {
      if ( size > (Size)data->size ) return exception( E_HEAPPROC_OFF );
    }

    if ( data->offs > 0 ) {
      if ( OFFSETADDOVFL( offset, data->offs ) ) return exception( E_INTOVFL );
      offset += data->offs;
    }

    if ( offset > OffsetMaxSize ) return exception( E_HEAPPROC_OFF );

    memcpy( addr + offset, buf, size );

  }

  return E_NONE;

}


static Status HeapMemResize
             (void *heapdata,
              Offset *oldsize,
              Offset newsize)

{
  HeapData *data = heapdata;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( oldsize == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( newsize < 0  ) ) return exception( E_ARGVAL );

  HeapDebugProc( "mem.resize", "size", newsize );

  if ( runcheck && ( data->handle == NULL ) ) return exception( E_HEAPPROC );

  if ( data->size > 0 ) return exception( E_HEAPPROC );

  if ( newsize > OffsetMaxSize ) return exception( E_HEAPPROC_OFF );

  if ( newsize < 1 ) newsize = 1;

  if ( newsize == *oldsize ) return E_NONE;

  Offset size = newsize;
  if ( data->offs > 0 ) {
    if ( OFFSETADDOVFL( size, data->offs ) ) return exception( E_INTOVFL );
    size += data->offs;
  }

  uint8_t *addr = realloc( data->handle, size );
  if ( addr == NULL ) return exception( E_MALLOC );

  data->handle = addr;

  *oldsize = newsize;

  return E_NONE;

}


static Status HeapMemFinal
              (void *heapdata,
               Status fail)

{
  HeapData *data = heapdata;

  HeapDebugProc( "mem.final", "stat", fail );

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );

  if ( data->size > 0 ) return exception( E_HEAPPROC );

  if ( data->handle != NULL ) free( data->handle );

  free( data );

  return E_NONE;

}


/* variables */

static const HeapProc HeapProcMemStruct = {
  HeapMemInit,
  HeapMemAddr,
  HeapMemRead,
  HeapMemWrite,
  HeapMemResize,
  NULL,
  NULL,
  NULL,
  HeapMemFinal,
};

const HeapProc *HeapProcMem = &HeapProcMemStruct;
