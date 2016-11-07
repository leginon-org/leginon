/*----------------------------------------------------------------------------*
*
*  ccfmodule.h  -  array: cross-correlation functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef ccfmodule_h_
#define ccfmodule_h_

#include "ccf.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module CcfModule;


/* construct linked list */

static ModuleListNode CcfModuleListNode = { NULL, ModuleListPtr, &CcfModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&CcfModuleListNode)


#endif
