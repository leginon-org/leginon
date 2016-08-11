/*----------------------------------------------------------------------------*
*
*  stringsmodule.h  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef stringsmodule_h_
#define stringsmodule_h_

#include "strings.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module StringsModule;


/* construct linked list */

static ModuleListNode StringsModuleListNode = { NULL, ModuleListPtr, &StringsModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&StringsModuleListNode)


#endif
