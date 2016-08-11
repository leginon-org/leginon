/*----------------------------------------------------------------------------*
*
*  transfmodule.h  -  core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef transfmodule_h_
#define transfmodule_h_

#include "transfdefs.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module TransfModule;


/* construct linked list */

static ModuleListNode TransfModuleListNode = { NULL, ModuleListPtr, &TransfModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TransfModuleListNode)


#endif
