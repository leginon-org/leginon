/*----------------------------------------------------------------------------*
*
*  transformmodule.h  -  array: spatial transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef transformmodule_h_
#define transformmodule_h_

#include "transform.h"
#include "module.h"


/* dependencies */

#include "statisticsmodule.h"
#include "transfermodule.h"


/* module descriptor */

extern const Module TransformModule;


/* construct linked list */

static ModuleListNode TransformModuleListNode = { NULL, ModuleListPtr, &TransformModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TransformModuleListNode)


#endif
