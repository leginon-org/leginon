/*----------------------------------------------------------------------------*
*
*  polarmodule.h  -  array: spatial polar transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef polarmodule_h_
#define polarmodule_h_

#include "polar.h"
#include "module.h"


/* dependencies */

#include "transformmodule.h"


/* module descriptor */

extern const Module PolarModule;


/* construct linked list */

static ModuleListNode PolarModuleListNode = { NULL, ModuleListPtr, &PolarModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&PolarModuleListNode)


#endif
