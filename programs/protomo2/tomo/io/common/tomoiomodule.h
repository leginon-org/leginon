/*----------------------------------------------------------------------------*
*
*  tomoiomodule.h  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoiomodule_h_
#define tomoiomodule_h_

#include "tomoio.h"
#include "module.h"


/* dependencies */

#include "tomomodule.h"
#include "tomometamodule.h"
#include "imageioextramodule.h"


/* module descriptor */

extern const Module TomoioModule;


/* construct linked list */

static ModuleListNode TomoioModuleListNode = { NULL, ModuleListPtr, &TomoioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomoioModuleListNode)


#endif
