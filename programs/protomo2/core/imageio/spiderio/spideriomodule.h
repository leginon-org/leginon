/*----------------------------------------------------------------------------*
*
*  spideriomodule.h  -  imageio: spider files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef spideriomodule_h_
#define spideriomodule_h_

#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module SpiderioModule;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode SpiderioModuleListNode = { NULL, ModuleListPtr, &SpiderioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&SpiderioModuleListNode)

#endif


#endif
