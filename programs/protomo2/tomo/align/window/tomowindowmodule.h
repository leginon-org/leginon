/*----------------------------------------------------------------------------*
*
*  tomowindowmodule.h  -  align: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomowindowmodule_h_
#define tomowindowmodule_h_

#include "tomowindow.h"
#include "module.h"


/* dependencies */

#include "windowmodule.h"
#include "windowfouriermodule.h"
#include "tomoparamreadmodule.h"
#include "convolmodule.h"


/* module descriptor */

extern const Module TomowindowModule;


/* construct linked list */

static ModuleListNode TomowindowModuleListNode = { NULL, ModuleListPtr, &TomowindowModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomowindowModuleListNode)


#endif
