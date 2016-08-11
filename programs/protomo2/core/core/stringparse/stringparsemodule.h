/*----------------------------------------------------------------------------*
*
*  stringparsemodule.h  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef stringparsemodule_h_
#define stringparsemodule_h_

#include "stringparse.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module StringParseModule;


/* construct linked list */

static ModuleListNode StringParseModuleListNode = { NULL, ModuleListPtr, &StringParseModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&StringParseModuleListNode)


#endif
