/*----------------------------------------------------------------------------*
*
*  stringformatmodule.h  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef stringformatmodule_h_
#define stringformatmodule_h_

#include "stringformat.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module StringFormatModule;


/* construct linked list */

static ModuleListNode StringFormatModuleListNode = { NULL, ModuleListPtr, &StringFormatModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&StringFormatModuleListNode)


#endif
