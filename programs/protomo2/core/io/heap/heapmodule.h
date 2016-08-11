/*----------------------------------------------------------------------------*
*
*  heapmodule.h  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef heapmodule_h_
#define heapmodule_h_

#include "heap.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module HeapModule;


/* construct linked list */

static ModuleListNode HeapModuleListNode = { NULL, ModuleListPtr, &HeapModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&HeapModuleListNode)


#endif
