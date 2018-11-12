/*----------------------------------------------------------------------------*
*
*  i3io.c  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3iocommon.h"
#include "heap.h"
#include "exception.h"


/* functions */

extern Status I3ioSegm
              (I3io *i3io,
               Offset size,
               I3ioMeta meta,
               int *segm)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( size < 0 ) )     return exception( E_ARGVAL );
  if ( argcheck( segm == NULL ) ) return exception( E_ARGVAL );

  status = HeapNew( (Heap *)i3io, size, meta, segm, NULL );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status I3ioAlloc
              (I3io *i3io,
               int segm, 
               Offset size,
               I3ioMeta meta)


{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( size < 0 ) ) return exception( E_ARGVAL );

  status = HeapAlloc( (Heap *)i3io, segm, size, meta, NULL );
  if ( exception( status ) ) return status;

  return E_NONE;

}

extern Status I3ioDealloc
              (I3io *i3io,
               int segm)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );

  status = HeapDealloc( (Heap *)i3io, segm );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status I3ioResize
              (I3io *i3io,
               int segm,
               Offset size)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( size < 0 ) ) return exception( E_ARGVAL );

  status = HeapResize( (Heap *)i3io, segm, size, NULL );
  if ( exception( status ) ) return status;


  return E_NONE;

}


extern Status I3ioAccess
               (I3io *i3io,
                int segm,
                Offset *offs,
                Offset *size,
                I3ioMeta *meta)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );

  Offset off, siz; HeapMeta met;

  status = HeapAccess( (Heap *)i3io, segm, &off, &siz, &met );
  if ( exception( status ) ) return status;

  if ( offs != NULL ) *offs = off;
  if ( size != NULL ) *size = siz;
  if ( meta != NULL ) *meta = met;

  return E_NONE;

}


extern Status I3ioMetaSet
              (I3io *i3io,
               int index,
               I3ioMeta meta)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( index < 0 ) ) return exception( E_ARGVAL );

  status = HeapMetaSet( (Heap *)i3io, index, meta );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status I3ioMetaGet
              (I3io *i3io,
               int index,
               I3ioMeta *meta)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( index < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( meta == NULL ) ) return exception( E_ARGVAL );

  status = HeapMetaGet( (Heap *)i3io, index, meta );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern I3ioMeta *I3ioFormat
                 (void *buf,
                  Size len)

{

  return HeapFormat( buf, len );

}
