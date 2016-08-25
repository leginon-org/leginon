/*----------------------------------------------------------------------------*
*
*  tomogeommodule.h  -  tomography: tilt geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomogeommodule_h_
#define tomogeommodule_h_

#include "tomogeom.h"
#include "module.h"


/* dependencies */

#include "tomotiltmodule.h"


/* module descriptor */

extern const Module TomogeomModule;


/* construct linked list */

static ModuleListNode TomogeomModuleListNode = { NULL, ModuleListPtr, &TomogeomModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomogeomModuleListNode)


#endif
