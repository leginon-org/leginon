/*----------------------------------------------------------------------------*
*
*  i3ioget.c  -  io: i3 input/output
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
#include "fileiochecksum.h"
#include "heapproccommon.h"
#include "exception.h"
#include <string.h>


/* functions */

extern const char *I3ioGetPath
                   (I3io *i3io)

{

  Heap *heap = (Heap *)i3io;
  if ( heap == NULL ) return NULL;
  HeapData *data = heap->data;

  while ( heap->stat & HeapStatNest ) {
    heap = data->handle;
    if ( heap == NULL ) return NULL;
    data = heap->data;
  }

  Fileio *fileio = data->handle;
  if ( fileio == NULL ) return NULL;

  return FileioGetFullPath( fileio );

}


extern Bool I3ioGetSwap
            (I3io *i3io)

{

  return HeapGetSwap( (Heap *)i3io );

}


extern IOMode I3ioGetMode
              (I3io *i3io)

{

  return HeapGetMode( (Heap *)i3io );

}


extern void I3ioGetTime
            (I3io *i3io,
             Time *cre,
             Time *mod)

{

  if ( HeapGetTime( (Heap *)i3io, cre, mod ) ) {

    if ( cre != NULL ) memset( cre, 0, sizeof(Time) );
    if ( mod != NULL ) memset( mod, 0, sizeof(Time) );

  }

}


extern Status I3ioGetChecksum
              (I3io *i3io,
               Size sumlen,
               uint8_t *sum)

{
  Status status;

  if ( i3io == NULL ) return exception( E_ARGVAL );
  if ( !sumlen ) return exception( E_ARGVAL );
  if ( sum == NULL ) return exception( E_ARGVAL );

  Heap *heap = (Heap *)i3io;
  if ( heap == NULL ) return exception( E_I3IO );
  HeapData *data = heap->data;

  while ( heap->stat & HeapStatNest ) {
    heap = data->handle;
    if ( heap == NULL ) return exception( E_I3IO );
    data = heap->data;
  }

  Fileio *fileio = data->handle;
  if ( fileio == NULL ) return exception( E_I3IO );

  status = FileioChecksum( fileio, ChecksumTypeXor, sumlen, sum );
  if ( exception( status ) ) return status;

  return E_NONE;

}
