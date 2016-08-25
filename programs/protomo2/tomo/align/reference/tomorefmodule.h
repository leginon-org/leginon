/*----------------------------------------------------------------------------*
*
*  tomorefmodule.h  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomorefmodule_h_
#define tomorefmodule_h_

#include "tomoref.h"
#include "module.h"


/* dependencies */

#include "tomoseriesmodule.h"
#include "tomoimagemodule.h"
#include "tomotransfermodule.h"
#include "tomoparamreadmodule.h"
#include "imagearraymodule.h"
#include "imagemaskmodule.h"
#include "threadmodule.h"
#include "windowmodule.h"
#include "windowfouriermodule.h"


/* module descriptor */

extern const Module TomorefModule;


/* construct linked list */

static ModuleListNode TomorefModuleListNode = { NULL, ModuleListPtr, &TomorefModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomorefModuleListNode)


#endif
