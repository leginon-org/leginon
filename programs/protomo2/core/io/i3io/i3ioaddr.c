/*----------------------------------------------------------------------------*
*
*  i3ioaddr.c  -  io: i3 input/output
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

extern Status I3ioAddr
              (I3io *i3io,
               int segm,
               Offset offs,
               Size size,
               void **addr)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( segm < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( offs < 0 ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );

  status = I3ioSet( i3io, segm, &offs, &size );
  if ( exception( status ) ) return status;

  Heap *heap = (Heap *)i3io;

  if ( heap->proc->addr == NULL ) {

    *addr = NULL;

  } else {

    status = heap->proc->addr( heap->data, offs, size, addr );
    if ( exception( status ) ) return status;

  }

  return E_NONE;

}
