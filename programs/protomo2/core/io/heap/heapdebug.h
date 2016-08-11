/*----------------------------------------------------------------------------*
*
*  heapdebug.h  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef heapdebug_h_
#define heapdebug_h_

#include "heap.h"
#include "message.h"
#include <stdio.h>


/* types */

typedef enum {
  HeapDebugModeMain = 0x01,
  HeapDebugModeComm = 0x02,
  HeapDebugModeProc = 0x04,
} HeapDebugMode;


/* macros */

#ifdef HEAPDEBUG

#define HeapDebugMain( f, m, n )  HeapDebugPrint( HeapDebugModeMain, f, m, n )

#define HeapDebugComm( f, m, n )  HeapDebugPrint( HeapDebugModeComm, f, m, n )

#define HeapDebugProc( f, m, n )  if ( heapdebug && ( HeapDebugFlags & HeapDebugModeProc ) ) MessageFormat( "%s:%-16.16s %-4.4s %-"OffsetD"\n", "*", "heap"f, m, (Offset)( n ) )

#define HeapDebugPrint( d, f, m, n )  if ( heapdebug && ( HeapDebugFlags & ( d ) ) ) MessageFormat( "%"SizeU":%-16.16s %-4.4s %-"OffsetD"\n", heap->objcount, "heap"f, m, (Offset)( n ) )

#else

#define HeapDebugMain( f, m, n )

#define HeapDebugComm( f, m, n )

#define HeapDebugProc( f, m, n )

#endif


/* variables */

#ifdef HEAPDEBUG

extern HeapDebugMode HeapDebugFlags;

#endif


/* prototypes */

#ifdef HEAPDEBUG

extern void HeapDebugSetMode
            (int mode);

#endif

extern Status HeapDump
              (FILE *stream,
               const Heap *heap);


#endif
