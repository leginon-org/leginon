/*----------------------------------------------------------------------------*
*
*  tomoimagemodule.h  -  align: image geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoimagemodule_h_
#define tomoimagemodule_h_

#include "tomoimage.h"
#include "module.h"


/* dependencies */

#include "tomoseriesmodule.h"
#include "matmodule.h"


/* module descriptor */

extern const Module TomoimageModule;


/* construct linked list */

static ModuleListNode TomoimageModuleListNode = { NULL, ModuleListPtr, &TomoimageModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomoimageModuleListNode)


#endif
