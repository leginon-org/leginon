/*----------------------------------------------------------------------------*
*
*  i3datamodule.h  -  io: i3 data
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef i3datamodule_h_
#define i3datamodule_h_

#include "i3data.h"
#include "module.h"


/* dependencies */

#include "imagemodule.h"
#include "statisticsmodule.h"


/* module descriptor */

extern const Module I3dataModule;


/* construct linked list */

static ModuleListNode I3dataModuleListNode = { NULL, ModuleListPtr, &I3dataModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&I3dataModuleListNode)


#endif
