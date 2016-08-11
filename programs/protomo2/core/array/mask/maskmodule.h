/*----------------------------------------------------------------------------*
*
*  maskmodule.h  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef maskmodule_h_
#define maskmodule_h_

#include "mask.h"
#include "module.h"


/* dependencies */

#include "arraymodule.h"
#include "statisticsmodule.h"


/* module descriptor */

extern const Module MaskModule;


/* construct linked list */

static ModuleListNode MaskModuleListNode = { NULL, ModuleListPtr, &MaskModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&MaskModuleListNode)


#endif
