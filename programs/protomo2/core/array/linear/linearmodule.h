/*----------------------------------------------------------------------------*
*
*  linearmodule.h  -  array: spatial linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef linearmodule_h_
#define linearmodule_h_

#include "linear.h"
#include "module.h"


/* dependencies */

#include "transformmodule.h"


/* module descriptor */

extern const Module LinearModule;


/* construct linked list */

static ModuleListNode LinearModuleListNode = { NULL, ModuleListPtr, &LinearModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&LinearModuleListNode)


#endif
