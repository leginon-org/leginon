/*----------------------------------------------------------------------------*
*
*  tomoparamreadmodule.h  -  core: retrieve parameters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoparamreadmodule_h_
#define tomoparamreadmodule_h_

#include "tomoparamread.h"
#include "module.h"


/* dependencies */

#include "tomoparammodule.h"
#include "ccfmodule.h"
#include "imageiomodule.h"
#include "matmodule.h"
#include "maskmodule.h"
#include "spatialmodule.h"
#include "transfermodule.h"
#include "transformmodule.h"
#include "windowmodule.h"


/* module descriptor */

extern const Module TomoparamReadModule;


/* construct linked list */

static ModuleListNode TomoparamReadModuleListNode = { NULL, ModuleListPtr, &TomoparamReadModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomoparamReadModuleListNode)


#endif
