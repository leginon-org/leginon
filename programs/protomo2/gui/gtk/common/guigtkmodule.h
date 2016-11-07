/*----------------------------------------------------------------------------*
*
*  guigtkmodule.h  -  guigtk: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef guigtkmodule_h_
#define guigtkmodule_h_

#include "guigtk.h"
#include "module.h"


/* dependencies */

#include "graphmodule.h"


/* module descriptor */

extern const Module GuigtkModule;


/* construct linked list */

static ModuleListNode GuigtkModuleListNode = { NULL, ModuleListPtr, &GuigtkModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&GuigtkModuleListNode)


#endif
