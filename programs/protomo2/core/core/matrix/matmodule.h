/*----------------------------------------------------------------------------*
*
*  matmodule.h  -  core: matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef matmodule_h_
#define matmodule_h_

#include "matdefs.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module MatModule;


/* construct linked list */

static ModuleListNode MatModuleListNode = { NULL, ModuleListPtr, &MatModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&MatModuleListNode)


#endif
