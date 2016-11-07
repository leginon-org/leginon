/*----------------------------------------------------------------------------*
*
*  threadmodule.h  -  core: posix threads
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef threadmodule_h_
#define threadmodule_h_

#include "thread.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module ThreadModule;


/* construct linked list */

static ModuleListNode ThreadModuleListNode = { NULL, ModuleListPtr, &ThreadModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ThreadModuleListNode)


#endif
