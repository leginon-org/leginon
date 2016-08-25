/*----------------------------------------------------------------------------*
*
*  fffiomodule.h  -  imageio: FFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fffiomodule_h_
#define fffiomodule_h_

#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module FFFioModule;


/* construct linked list */

static ModuleListNode FFFioModuleListNode = { NULL, ModuleListPtr, &FFFioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&FFFioModuleListNode)


#endif
