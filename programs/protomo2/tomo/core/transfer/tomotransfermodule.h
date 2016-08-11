/*----------------------------------------------------------------------------*
*
*  tomotransfermodule.h  -  tomography: transfer functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomotransfermodule_h_
#define tomotransfermodule_h_

#include "tomotransfer.h"
#include "module.h"


/* dependencies */

#include "tomoparamreadmodule.h"
#include "matmodule.h"
#include "threadmodule.h"


/* module descriptor */

extern const Module TomotransferModule;


/* construct linked list */

static ModuleListNode TomotransferModuleListNode = { NULL, ModuleListPtr, &TomotransferModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr ( &TomotransferModuleListNode )


#endif
