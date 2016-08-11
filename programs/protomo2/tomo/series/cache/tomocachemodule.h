/*----------------------------------------------------------------------------*
*
*  tomocachemodule.h  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomocachemodule_h_
#define tomocachemodule_h_

#include "tomocache.h"
#include "module.h"


/* dependencies */

#include "i3iomodule.h"


/* module descriptor */

extern const Module TomocacheModule;


/* construct linked list */

static ModuleListNode TomocacheModuleListNode = { NULL, ModuleListPtr, &TomocacheModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomocacheModuleListNode)


#endif
