/*----------------------------------------------------------------------------*
*
*  heapdebug.c  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "heapdebugcommon.h"
#include "stringformat.h"
#include "exception.h"
#include <stdlib.h>


/* variables */

#ifdef HEAPDEBUG
Bool HeapDebug = True;
HeapDebugMode HeapDebugFlags = 0;
#endif


/* functions */

extern void HeapDebugSetMode
            (int mode)

{

#ifdef HEAPDEBUG

  HeapDebugFlags = mode;

#endif

}


static void HeapGetMagic
            (HeapAtom magic,
             Size bufsize,
             char *buf)

{

  if ( !bufsize-- ) return;

  for ( Size i = 0; i < 8; i++ ) {
    if ( !bufsize ) break;
    *buf++ = magic;
    magic >>= 8;
  }

  *buf = 0;

}


static void HeapGetVers
            (HeapAtom vers,
             Size bufsize,
             char *buf)

{

  if ( !bufsize-- ) return;

  for ( Size i = 0; i < 16; i++ ) {
    if ( !bufsize ) break;
    char c = vers & 0x0f;
    if ( c == 15 ) break;
    *buf++ = ( c < 10 ) ? '0' + c : '.';
    vers >>= 4;
  }

  *buf = 0;

}


extern Status HeapDebugDump
              (FILE *stream,
               const HeapAtom *hdr,
               const HeapAtom *dir)

{
#define bufsize 128
  char buf[bufsize];
  Size size;

  fflush( stream );
  HeapGetMagic( hdr[0], bufsize, buf );
  fprintf( stream, "hdr[0] = \"%s\"\n", buf );
  HeapGetVers( hdr[1], bufsize, buf );
  fprintf( stream, "hdr[1] = \"%s\"\n", buf );
  fprintf( stream, "hdr[2] = %"HeapAtomU"\n", hdr[2] );
  fprintf( stream, "hdr[3] = %"HeapAtomU"\n", hdr[3] );
  fprintf( stream, "hdr[4] = %"HeapAtomU"\n", hdr[4] );
  fprintf( stream, "hdr[5] = %"HeapAtomX"\n", hdr[5] );
  size = bufsize; StringFormatDateTime( (const Time *)( hdr + 6 ), NULL, &size, buf );
  fprintf( stream, "hdr[6] = %s\n", buf );
  size = bufsize; StringFormatDateTime( (const Time *)( hdr + 7 ), NULL, &size, buf );
  fprintf( stream, "hdr[7] = %s\n", buf );
  fprintf( stream, "meta =" );
  for ( Size i = HeapMetaMin; i < HeapHdrSize; i++ ) {
    fprintf( stream, " %"HeapAtomU, hdr[i] );
  }
  fprintf( stream, "\n" );

  if ( dir == NULL ) {
    fprintf( stream, "dir = NULL\n" ); goto exit;
  }
  fprintf( stream, "dir[0] = %"HeapAtomU"\n", *dir );
  if ( !HeapDirCount ) goto exit;

  fprintf( stream, "segm  ent    prev  next        offset       alloc        size       size8        meta\n" );
  for ( HeapIndex i = 0; i < HeapDirCount; i++ ) {
    HeapIndex j = i * HeapEntSize;
    HeapIndex prev = DirPrev( j ), next = DirNext( j );
    HeapAtom link = DirLink( j ), offs = DirOffs( j );
    HeapAtom size = DirSize( j ), meta = DirMeta( j );
    HeapAtom atoms = ( size + sizeof(HeapAtom) - 1 ) / sizeof(HeapAtom);
    HeapAtom nextoffs = next ? DirOffs( next ) : offs;
    HeapAtom alloc = nextoffs - offs;
    char stat = ' ';
    switch ( i ) {
      case 0:  fprintf( stream, " hdr" ); break;
      case 1:  fprintf( stream, " end" ); break;
      case 2:  fprintf( stream, " dir" ); break;
      default: {
        fprintf( stream, "%4"HeapIndexU, i - 3 );
        if ( link ) {
          if ( size == 0 ) {
            stat = '*';
          } else if ( size < sizeof(HeapAtom) ) {
            stat = '?';
          } else if ( size == sizeof(HeapAtom) ) {
            stat = ':';
          }
        } else {
          if ( offs || size ) stat = '?';
        }
      }
    }
    fprintf( stream, " %4"HeapIndexU"   ", j );
    if ( DirLink( j ) ) {
      fprintf( stream, "[%4"HeapIndexU",%4"HeapIndexU" ]", prev, next );
    } else {
      fprintf( stream, "[          ]" );
    }
    fprintf( stream, "%c %11"HeapAtomU" %11"HeapAtomU" %11"HeapAtomU" %11"HeapAtomU" %11"HeapAtomX"\n", stat, offs, alloc, atoms, size, meta );
  }

  exit:
  fflush( stream );

  return E_NONE;

}


extern Status HeapDump
              (FILE *stream,
               const Heap *heap)

{

  return HeapDebugDump( stream, heap->hdr, heap->dir );

}
