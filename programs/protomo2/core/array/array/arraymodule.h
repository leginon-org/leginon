/*----------------------------------------------------------------------------*
*
*  arraymodule.h  -  array: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef arraymodule_h_
#define arraymodule_h_

#include "array.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module ArrayModule;


/* construct linked list */

static ModuleListNode ArrayModuleListNode = { NULL, ModuleListPtr, &ArrayModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ArrayModuleListNode)


#endif
