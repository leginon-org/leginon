/*----------------------------------------------------------------------------*
*
*  tomodiagnmodule.h  -  align: diagnostic output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomodiagnmodule_h_
#define tomodiagnmodule_h_

#include "tomodiagn.h"
#include "module.h"


/* dependencies */

#include "tomoseriesmodule.h"
#include "imageiomodule.h"


/* module descriptor */

extern const Module TomodiagnModule;


/* construct linked list */

static ModuleListNode TomodiagnModuleListNode = { NULL, ModuleListPtr, &TomodiagnModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomodiagnModuleListNode)


#endif
