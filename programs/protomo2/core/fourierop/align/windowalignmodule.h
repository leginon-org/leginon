/*----------------------------------------------------------------------------*
*
*  windowalignmodule.h  -  fourierop: window alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef windowalignmodule_h_
#define windowalignmodule_h_

#include "windowalign.h"
#include "module.h"


/* dependencies */

#include "windowmodule.h"
#include "windowfouriermodule.h"


/* module descriptor */

extern const Module WindowAlignModule;


/* construct linked list */

static ModuleListNode WindowAlignModuleListNode = { NULL, ModuleListPtr, &WindowAlignModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&WindowAlignModuleListNode)


#endif
