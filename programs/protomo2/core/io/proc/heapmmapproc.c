/*----------------------------------------------------------------------------*
*
*  heapmmapproc.c  -  io: heap procedures
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
#include "exception.h"
#include "macros.h"
#include <string.h>


/* functions */

static void *HeapMmapGetAddr
             (HeapData *data,
              Offset offset,
              Size size)

{
  Offset mapoffs = 0;
  Size mapsize = 0;
  Status status;

  if ( runcheck && ( data->handle == NULL ) ) { exception( E_HEAPPROC ); return NULL; }

  if ( size > (Size)OffsetMaxSize ) { exception( E_HEAPPROC_OFF ); return NULL; }

  if ( data->size > 0 ) {
    if ( size > (Size)data->size ) { exception( E_HEAPPROC_OFF ); return NULL; }
    mapsize = data->size;
  }

  if ( data->offs > 0 ) {
    if ( OFFSETADDOVFL( offset, data->offs ) ) { exception( E_INTOVFL ); return NULL; }
    offset += data->offs;
    mapoffs = data->offs;
  }

  status = FileioMap( data->handle, mapoffs, mapsize );
  if ( !exception( status ) ) {
    return FileioGetAddr( data->handle );
  }

  status = FileioMap( data->handle, offset, size );
  if ( exception( status ) ) return NULL;

  return FileioGetAddr( data->handle );

}


static Status HeapMmapAddr
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

  void *addr = HeapMmapGetAddr( data, offset, size );
  if ( addr == NULL ) return exception( E_HEAPPROC_MMP );

  *buf = addr;

  return E_NONE;

}


static Status HeapMmapRead
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

  if ( size ) {

    void *addr = HeapMmapGetAddr( data, offset, size );
    if ( addr == NULL ) return exception( E_HEAPPROC_MMP );

    memcpy( buf, addr, size );

  }

  return E_NONE;

}


static Status HeapMmapWrite
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

  if ( size ) {

    void *addr = HeapMmapGetAddr( data, offset, size );
    if ( addr == NULL ) return exception( E_HEAPPROC_MMP );

    memcpy( addr, buf, size );

  }

  return E_NONE;

}


static Status HeapMmapResize
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

  status = FileioUnmap( data->handle );
  if ( exception( status ) ) return status;

  status = HeapFileResizeSub( data, oldsize, newsize );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern const HeapProc *HeapProcGetMmap
                       (const HeapFileProc *proc)

{
  static const HeapProc HeapProcMmap = {
    NULL,
    HeapMmapAddr,
    HeapMmapRead,
    HeapMmapWrite,
    HeapMmapResize,
    NULL,
    NULL,
    HeapFileSync,
    HeapFileFinal,
  };

  return ( proc == NULL ) ? &HeapProcMmap : ( proc->mmap == NULL ) ? HeapProcNull : proc->mmap;

}
