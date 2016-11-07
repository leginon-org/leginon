/*----------------------------------------------------------------------------*
*
*  parsemodule.h  -  core: auxiliary parser routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef parsemodule_h_
#define parsemodule_h_

#include "parse.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module ParseModule;


/* construct linked list */

static ModuleListNode ParseModuleListNode = { NULL, ModuleListPtr, &ParseModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ParseModuleListNode)


#endif
