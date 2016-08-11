/*----------------------------------------------------------------------------*
*
*  iomodule.h  -  io: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef iomodule_h_
#define iomodule_h_

#include "io.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module IOModule;


/* construct linked list */

static ModuleListNode IOModuleListNode = { NULL, ModuleListPtr, &IOModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&IOModuleListNode)


#endif
