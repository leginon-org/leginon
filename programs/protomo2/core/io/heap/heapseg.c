/*----------------------------------------------------------------------------*
*
*  heapseg.c  -  io: heap management
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
#include <string.h>


/* functions */

extern Status HeapSegSearch
              (const HeapAtom *dir,
               HeapAtom dircount,
               HeapAtom size,
               HeapIndex *entr,
               HeapIndex *free,
               HeapAtom *offs,
               HeapAtom *allo)

{

  if ( argcheck( dir == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( size > HeapSegMax ) ) return exception( E_ARGVAL );

  HeapIndex ent = 0;
  HeapIndex min = 0; HeapAtom minoffs = 0, minsize = HeapSegMax;
  size = ( size + sizeof(HeapAtom) - 1 ) / sizeof(HeapAtom);

  for ( HeapIndex i = HeapSegInd; i < dircount * HeapEntSize; i += HeapEntSize ) {

    if ( !DirLink( i ) ) {

      ent = i;

    } else if ( !DirSize( i ) ) {

      HeapIndex nxt = DirNext( i );
      HeapAtom curoffs = DirOffs( i ), nxtoffs = DirOffs( nxt );
      if ( nxtoffs < curoffs ) return exception( E_HEAP_ERR );

      HeapAtom cursize = nxtoffs - curoffs;
      if ( cursize >= size ) {
        if ( cursize == size ) {
          if ( entr != NULL ) *entr = 0;
          if ( free != NULL ) *free = i;
          if ( offs != NULL ) *offs = curoffs;
          if ( allo != NULL ) *allo = cursize;
          return E_NONE;
        }
        if ( cursize < minsize ) {
          min = i;
          minoffs = curoffs;
          minsize = cursize;
        }
      }

    }

  }

  if ( entr != NULL ) *entr = ent;
  if ( free != NULL ) *free = min;
  if ( offs != NULL ) *offs = minoffs;
  if ( allo != NULL ) *allo = min ? minsize : 0;

  return E_NONE;

}


extern void HeapSegMerge
            (HeapAtom *dir)

{

  HeapIndex ind = DirNext( HeapHdrInd );

  while ( ind != HeapEndInd ) {

    HeapIndex nxt = DirNext( ind );

    if ( !DirSize( ind ) ) {

      while ( ( nxt != HeapEndInd ) && !DirSize( nxt ) ) {
        HeapIndex seg = DirNext( nxt );
        ClrEnt( nxt );
        nxt = seg;
      }

      SetPrev( nxt, ind );
      SetNext( ind, nxt );

    }

    ind = nxt;

  }

}


extern void HeapSegSplit
            (HeapAtom *dir,
             HeapIndex ent,
             HeapIndex seg,
             HeapAtom size,
             HeapAtom allo)

{

  size = ( size + sizeof(HeapAtom) - 1 ) / sizeof(HeapAtom);

  if ( ( allo > size ) && ( ( allo - size ) >= HeapEntMin ) ) {

      HeapIndex nxt = DirNext( seg );
      SetPrev( nxt, ent );
      SetNext( seg, ent );
      SetEnt( ent, seg, nxt, DirOffs( seg ) + size, 0, 0 );

  }

}


extern void HeapSegSwap
            (HeapAtom *dir,
             HeapIndex ind1,
             HeapIndex ind2,
             HeapAtom size2,
             HeapAtom meta2)

{
  HeapIndex i, p, n, tab[6];
  HeapAtom a;

  tab[0] = ind1;
  tab[1] = DirPrev( ind1 );
  tab[2] = DirNext( ind1 );

  if ( tab[1] || tab[2] ) {

    tab[3] = DirPrev( ind2 );

    if ( ( tab[3] == tab[2] ) || ( tab[3] == tab[1] ) || ( tab[3] == tab[0] ) ) {

      tab[3] = DirNext( ind2 );

      if ( ( tab[3] == tab[2] ) || ( tab[3] == tab[1] ) || ( tab[3] == tab[0] ) ) {
        i = 3;
      } else {
        i = 4;
      }

    } else {

      tab[4] = DirNext( ind2 );

      if ( ( tab[4] == tab[2] ) || ( tab[4] == tab[1] ) || ( tab[4] == tab[0] ) ) {
        i = 4;
      } else {
        i = 5;
      }

    }

    if ( ( ind2 != tab[2] ) && ( ind2 != tab[1] ) ) {
      tab[i++] = ind2;
    }

  } else {

    tab[1] = DirPrev( ind2 );

    if ( tab[1] == tab[0] ) {

      tab[1] = DirNext( ind2 );

      if ( tab[1] == tab[0] ) {
        i = 1;
      } else {
        i = 2;
      }

    } else {

      tab[2] = DirNext( ind2 );

      if ( tab[2] == tab[0] ) {
        i = 2;
      } else {
        i = 3;
      }

    }

    tab[i++] = ind2;

  }

  while ( i-- ) {

    p = DirPrev( tab[i] );
    if ( p == ind1 ) {
      p = ind2;
    } else if ( p == ind2 ) {
      p = ind1;
    }

    n = DirNext( tab[i] );
    if ( n == ind1 ) {
      n = ind2;
    } else if ( n == ind2 ) {
      n = ind1;
    }

    DirLink( tab[i] ) = HeapLink( p, n );

  }

  a = DirLink( ind1 ); DirLink( ind1 ) = DirLink( ind2 ); DirLink( ind2 ) = a;
  a = DirOffs( ind1 ); DirOffs( ind1 ) = DirOffs( ind2 ); DirOffs( ind2 ) = a;

  DirSize( ind1 ) = size2; DirMeta( ind1 ) = meta2;
  DirSize( ind2 ) = 0;     DirMeta( ind2 ) = 0;

}
