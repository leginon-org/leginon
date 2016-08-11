/*----------------------------------------------------------------------------*
*
*  stringtablemodule.h  -  core: character string table
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef stringtablemodule_h_
#define stringtablemodule_h_

#include "stringtable.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module StringTableModule;


/* construct linked list */

static ModuleListNode StringTableModuleListNode = { NULL, ModuleListPtr, &StringTableModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&StringTableModuleListNode)


#endif
