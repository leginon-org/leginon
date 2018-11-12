/*----------------------------------------------------------------------------*
*
*  spatialmodule.h  -  array: spatial operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef spatialmodule_h_
#define spatialmodule_h_

#include "spatial.h"
#include "module.h"


/* dependencies */

#include "arraymodule.h"


/* module descriptor */

extern const Module SpatialModule;


/* construct linked list */

static ModuleListNode SpatialModuleListNode = { NULL, ModuleListPtr, &SpatialModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&SpatialModuleListNode)


#endif
