/*----------------------------------------------------------------------------*
*
*  heapprocmodule.h  -  io: heap procedures
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef heapprocmodule_h_
#define heapprocmodule_h_

#include "heapproc.h"
#include "module.h"


/* dependencies */

#include "heapmodule.h"
#include "fileiomodule.h"


/* module descriptor */

extern const Module HeapProcModule;


/* construct linked list */

static ModuleListNode HeapProcModuleListNode = { NULL, ModuleListPtr, &HeapProcModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&HeapProcModuleListNode)


#endif
