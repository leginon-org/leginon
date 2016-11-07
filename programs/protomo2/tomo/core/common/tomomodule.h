/*----------------------------------------------------------------------------*
*
*  tomomodule.h  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomomodule_h_
#define tomomodule_h_

#include "tomo.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module TomoModule;


/* construct linked list */

static ModuleListNode TomoModuleListNode = { NULL, ModuleListPtr, &TomoModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomoModuleListNode)


#endif
