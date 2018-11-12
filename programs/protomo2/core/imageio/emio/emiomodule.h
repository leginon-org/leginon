/*----------------------------------------------------------------------------*
*
*  emiomodule.h  -  imageio: em files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef emiomodule_h_
#define emiomodule_h_

#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module EMioModule;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode EMioModuleListNode = { NULL, ModuleListPtr, &EMioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&EMioModuleListNode)

#endif


#endif
