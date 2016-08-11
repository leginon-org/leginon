/*----------------------------------------------------------------------------*
*
*  graphmodule.h  -  graph: opengl graphics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef graphmodule_h_
#define graphmodule_h_

#include "graph.h"
#include "module.h"


/* dependencies */

#include "stringparsemodule.h"


/* module descriptor */

extern const Module GraphModule;


/* construct linked list */

static ModuleListNode GraphModuleListNode = { NULL, ModuleListPtr, &GraphModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&GraphModuleListNode)


#endif
