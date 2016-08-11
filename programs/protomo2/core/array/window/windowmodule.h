/*----------------------------------------------------------------------------*
*
*  windowmodule.h  -  window: image window
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef windowmodule_h_
#define windowmodule_h_

#include "window.h"
#include "module.h"


/* dependencies */

#include "maskmodule.h"
#include "linearmodule.h"
#include "samplemodule.h"
#include "statisticsmodule.h"
#include "transfermodule.h"


/* module descriptor */

extern const Module WindowModule;


/* construct linked list */

static ModuleListNode WindowModuleListNode = { NULL, ModuleListPtr, &WindowModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&WindowModuleListNode)


#endif
