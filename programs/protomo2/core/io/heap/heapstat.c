/*----------------------------------------------------------------------------*
*
*  heapstat.c  -  io: heap management
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

extern Status HeapStatSegm
              (Heap *heap,
               Offset *num,
               Offset *min,
               Offset *max,
               Offset *tot)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  HeapAtom *tmp = heap->tmp;

  status = HeapDirCheck( heap->hdr, heap->dir, tmp );
  if ( exception( status ) ) return status;

  if ( num != NULL ) *num = tmp[0];
  if ( min != NULL ) *min = tmp[1];
  if ( max != NULL ) *max = tmp[2];
  if ( tot != NULL ) *tot = tmp[3];

  return E_NONE;

}


extern Status HeapStatAlloc
              (Heap *heap,
               Offset *num,
               Offset *min,
               Offset *max,
               Offset *tot)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  HeapAtom *tmp = heap->tmp;

  status = HeapDirCheck( heap->hdr, heap->dir, tmp );
  if ( exception( status ) ) return status;

  if ( num != NULL ) *num = tmp[4];
  if ( min != NULL ) *min = tmp[5];
  if ( max != NULL ) *max = tmp[6];
  if ( tot != NULL ) *tot = tmp[7];

  return E_NONE;

}


extern Status HeapStatFree
              (Heap *heap,
               Offset *num,
               Offset *min,
               Offset *max,
               Offset *tot)

{
  Status status;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  HeapAtom *tmp = heap->tmp;

  status = HeapDirCheck( heap->hdr, heap->dir, tmp );
  if ( exception( status ) ) return status;

  if ( num != NULL ) *num = tmp[8];
  if ( min != NULL ) *min = tmp[9];
  if ( max != NULL ) *max = tmp[10];
  if ( tot != NULL ) *tot = tmp[11];

  return E_NONE;

}
