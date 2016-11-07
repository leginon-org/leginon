/*----------------------------------------------------------------------------*
*
*  i3ioarray.c  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3ioarray.h"
#include "i3iocommon.h"
#include "heap.h"
#include "exception.h"
#include "baselib.h"
#include "macros.h"
#include <stdlib.h>


/* functions */

extern Status I3ioArrayAlloc
              (I3io *i3io,
               int segm,
               Size length,
               Size elsize)

{
  Size siz;
  Status status;

  status = MulSize( length, elsize, &siz );
  if ( status ) return exception( E_I3IO_LEN );

  Heap *heap = (Heap *)i3io;

  status = HeapAlloc( heap, segm, siz, 0, NULL );
  if ( exception( status ) ) return status;

  return E_NONE;

}


static Status I3ioArraySet
              (I3io *i3io,
               int segm,
               Size offset,
               Size length,
               Size elsize,
               Offset *offs,
               Size *size)

{
  Offset off; Size siz;
  Status status;

  status = I3ioSet( i3io, segm, &off, &siz );
  if ( exception( status ) ) return status;

  status = MulSize( offset, elsize, &offset );
  if ( status ) return exception( E_I3IO_OFF );
  if ( offset >= siz ) return exception( E_I3IO_OFF );
  if ( OFFSETADDOVFL( off, (Offset)offset ) ) return exception( E_I3IO_OFF );

  status = MulSize( length, elsize, &length );
  if ( status ) return exception( E_I3IO_LEN );
  offset += length;
  if ( offset < length ) return exception( E_I3IO_LEN );
  if ( offset > siz ) return exception( E_I3IO_LEN );

  *offs = off + offset;
  *size = length;

  return E_NONE;

}


static Status I3ioArraySwap
              (Size length,
               Size elsize,
               const void *src,
               void *dst)

{

  switch ( elsize ) {
    case 2: Swap16( length, src, dst ); break;
    case 4: Swap32( length, src, dst ); break;
    case 8: Swap64( length, src, dst ); break;
    default: return E_I3IO;
  }

  return E_NONE;

}


extern Status I3ioArrayRead
              (I3io *i3io,
               int segm,
               Size offset,
               Size length,
               Size elsize,
               void *buf)

{
  Offset off; Size siz;
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( buf == NULL ) ) return exception( E_ARGVAL );

  status = I3ioArraySet( i3io, segm, offset, length, elsize, &off, &siz );
  if ( exception( status ) ) return status;

  Heap *heap = (Heap *)i3io;

  status = heap->proc->read( heap->data, off, siz, buf );
  if ( exception( status ) ) return status;

  if ( ( elsize > 1 ) && I3ioGetSwap( i3io ) ) {
    status = I3ioArraySwap( length, elsize, buf, buf );
    if ( exception( status ) ) return status;
  }

  return E_NONE;

}


extern void *I3ioArrayReadBuf
             (I3io *i3io,
              int segm,
              Size offset,
              Size length,
              Size elsize)

{
  Offset off; Size siz;
  Status status;

  if ( argcheck( i3io == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( segm < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }

  status = I3ioArraySet( i3io, segm, offset, length, elsize, &off, &siz );
  if ( pushexception( status ) ) return NULL;

  void *buf = malloc( siz ? siz : 1 );
  if ( buf == NULL ) {
    pushexception( E_MALLOC ); return NULL;
  }

  Heap *heap = (Heap *)i3io;

  status = heap->proc->read( heap->data, off, siz, buf );
  if ( pushexception( status ) ) { free( buf ); return NULL; }

  if ( ( elsize > 1 ) && I3ioGetSwap( i3io ) ) {
    status = I3ioArraySwap( length, elsize, buf, buf );
    if ( pushexception( status ) ) { free( buf ); return NULL; }
  }

  return buf;

}


extern Status I3ioArrayWrite
              (I3io *i3io,
               int segm,
               Size offset,
               Size length,
               Size elsize,
               const void *buf)

{
  #define buflen 1024
  uint8_t stackbuf[buflen];
  void *bufptr, *heapbuf = NULL;
  Offset off; Size siz;
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( buf == NULL ) ) return exception( E_ARGVAL );

  status = I3ioArraySet( i3io, segm, offset, length, elsize, &off, &siz );
  if ( exception( status ) ) return status;

  if ( ( elsize > 1 ) && I3ioGetSwap( i3io ) ) {
    if ( siz > buflen ) {
      heapbuf = malloc( siz );
      if ( heapbuf == NULL ) return exception( E_MALLOC );
      bufptr = heapbuf;
    } else {
      bufptr = stackbuf;
    }
    status = I3ioArraySwap( length, elsize, buf, bufptr );
    if ( exception( status ) ) goto exit;
    buf = bufptr;
  }

  Heap *heap = (Heap *)i3io;

  status = heap->proc->write( heap->data, off, siz, buf );
  if ( exception( status ) ) return status;

  exit:

  if ( heapbuf != NULL ) free( heapbuf );

  return status;

}


extern Status I3ioArrayWriteAlloc
              (I3io *i3io,
               int segm,
               Size length,
               Size elsize,
               const void *buf)

{
  Offset off; Size siz;
  Status stat, status;

  status = MulSize( length, elsize, &siz );
  if ( status ) return exception( E_I3IO_LEN );

  Heap *heap = (Heap *)i3io;

  status = HeapAlloc( heap, segm, siz, 0, &off );
  if ( exception( status ) ) return status;

  status = heap->proc->write( heap->data, off, siz, buf );
  if ( exception( status ) ) goto error;

  return E_NONE;

  error:

  stat = HeapDealloc( heap, segm );
  logexception( stat );

  return status;

}
