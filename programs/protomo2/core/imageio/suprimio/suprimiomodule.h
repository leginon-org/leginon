/*----------------------------------------------------------------------------*
*
*  suprimiomodule.h  -  imageio: suprim files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef suprimiomodule_h_
#define suprimiomodule_h_

#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module SuprimioModule;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode SuprimioModuleListNode = { NULL, ModuleListPtr, &SuprimioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&SuprimioModuleListNode)

#endif


#endif
