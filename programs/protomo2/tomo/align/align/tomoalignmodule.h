/*----------------------------------------------------------------------------*
*
*  tomoalignmodule.h  -  align: series alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoalignmodule_h_
#define tomoalignmodule_h_

#include "tomoalign.h"
#include "module.h"


/* dependencies */

#include "tomowindowmodule.h"
#include "tomodiagnmodule.h"
#include "tomorefmodule.h"
#include "tomoparamreadmodule.h"
#include "imagearraymodule.h"
#include "nmminmodule.h"
#include "threadmodule.h"


/* module descriptor */

extern const Module TomoalignModule;


/* construct linked list */

static ModuleListNode TomoalignModuleListNode = { NULL, ModuleListPtr, &TomoalignModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomoalignModuleListNode)


#endif
