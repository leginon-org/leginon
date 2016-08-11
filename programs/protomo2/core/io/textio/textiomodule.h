/*----------------------------------------------------------------------------*
*
*  textiomodule.h  -  io: text file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef textiomodule_h_
#define textiomodule_h_

#include "textio.h"
#include "module.h"


/* dependencies */

#include "stringparsemodule.h"


/* module descriptor */

extern const Module TextioModule;


/* construct linked list */

static ModuleListNode TextioModuleListNode = { NULL, ModuleListPtr, &TextioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TextioModuleListNode)


#endif
