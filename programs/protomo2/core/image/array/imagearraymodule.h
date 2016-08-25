/*----------------------------------------------------------------------------*
*
*  imagearraymodule.h  -  image: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagearraymodule_h_
#define imagearraymodule_h_

#include "imagearray.h"
#include "module.h"


/* dependencies */

#include "imagemodule.h"


/* module descriptor */

extern const Module ImageArrayModule;


/* construct linked list */

static ModuleListNode ImageArrayModuleListNode = { NULL, ModuleListPtr, &ImageArrayModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ImageArrayModuleListNode)


#endif
