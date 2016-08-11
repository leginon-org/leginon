/*----------------------------------------------------------------------------*
*
*  heapget.c  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "heapcommon.h"
#include "exception.h"
#include <string.h>


/* functions */

extern Bool HeapGetSwap
            (Heap *heap)

{

  if ( heap == NULL ) return False;
  if ( heap->stat & HeapStatPack ) return True;
  return False;

}


extern IOMode HeapGetMode
              (Heap *heap)

{

  return ( heap == NULL ) ? 0 : heap->mode;

}


extern Status HeapGetTime
              (Heap *heap,
               Time *cre,
               Time *mod)

{

  if ( heap == NULL ) return exception( E_ARGVAL );

  if ( cre != NULL ) {
    memcpy( cre, heap->hdr + 6, sizeof(Time) );
  }

  if ( mod != NULL ) {
    memcpy( mod, heap->hdr + 7, sizeof(Time) );
  }

  return E_NONE;

}


extern Offset HeapGetSize
              (Heap *heap)

{

  return ( heap == NULL ) ? -1 : heap->size;

}
