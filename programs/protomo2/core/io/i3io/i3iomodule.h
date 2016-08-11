/*----------------------------------------------------------------------------*
*
*  i3iomodule.h  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef i3iomodule_h_
#define i3iomodule_h_

#include "i3io.h"
#include "module.h"


/* dependencies */

#include "heapprocmodule.h"


/* module descriptor */

extern const Module I3ioModule;


/* construct linked list */

static ModuleListNode I3ioModuleListNode = { NULL, ModuleListPtr, &I3ioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&I3ioModuleListNode)


#endif
