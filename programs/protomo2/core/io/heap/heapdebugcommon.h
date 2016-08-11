/*----------------------------------------------------------------------------*
*
*  heapdebugcommon.h  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef heapdebugcommon_h_
#define heapdebugcommon_h_

#include "heapdebug.h"
#include "heapcommon.h"


/* prototypes */

extern Status HeapDebugDump
              (FILE *stream,
               const HeapAtom *hdr,
               const HeapAtom *dir);

#endif
