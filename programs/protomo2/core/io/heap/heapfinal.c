/*----------------------------------------------------------------------------*
*
*  heapfinal.c  -  io: heap management
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
#include "heapdebug.h"
#include "exception.h"
#include <stdlib.h>


#include <stdio.h>


/* functions */

extern Status HeapFinal
              (Heap *heap,
               Status fail)

{
  Status stat, status = E_NONE;

  if ( argcheck( heap == NULL ) ) return exception( E_ARGVAL );

  HeapAtom *hdr = heap->hdr;
  HeapAtom *dir = heap->dir;

  HeapDebugMain( ".final", "stat", fail );

  if ( !fail && ( heap->mode & IOWr ) ) {

    if ( heap->stat & HeapStatDbuf ) {

      HeapIndex new, spl;
      HeapAtom newoffs, newalloc, newsize = HeapDirSize * sizeof(HeapAtom);
      stat = HeapSegSearch( dir, HeapDirCount, newsize, &spl, &new, &newoffs, &newalloc );
      if ( exception( stat ) ) { status = stat; goto exit; }

      if ( !new ) {
        new = HeapDirInd; spl = 0;
        stat = HeapExtend( heap, hdr, dir, newsize, &new, &newoffs, &newalloc );
        if ( exception( stat ) ) { status = stat; goto exit; }
      }

      if ( new == HeapDirInd ) {

        DirSize( HeapDirInd ) = newsize;

      } else {

        HeapSegSwap( dir, HeapDirInd, new, newsize, 0 );

        if ( spl ) {
          HeapSegSplit( dir, spl, HeapDirInd, newsize, newalloc );
        }

      }

      HeapDirOffs = dir[0] = newoffs;

    }

    stat = HeapSync( heap, hdr, dir );
    if ( exception( stat ) ) { status = stat; goto exit; }

    stat = HeapHdrSync( heap, hdr, HeapStatOpen );
    if ( exception( stat ) ) { status = stat; goto exit; }

  }

  exit:

  if ( heap->nestcount ) {
    status = exception( E_HEAP_FIN );
  }

  stat = heap->proc->final( heap->data, status ? status : fail );
  if ( exception( stat ) ) status = stat;

  free( dir );
  free( heap );

  return status;

}
