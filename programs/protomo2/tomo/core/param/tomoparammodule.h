/*----------------------------------------------------------------------------*
*
*  tomoparammodule.h  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoparammodule_h_
#define tomoparammodule_h_

#include "tomoparam.h"
#include "module.h"


/* dependencies */

#include "parsemodule.h"
#include "iomodule.h"
#include "matmodule.h"
#include "stringsmodule.h"
#include "stringparsemodule.h"
#include "stringtablemodule.h"


/* module descriptor */

extern const Module TomoparamModule;


/* construct linked list */

static ModuleListNode TomoparamModuleListNode = { NULL, ModuleListPtr, &TomoparamModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr ( &TomoparamModuleListNode )


#endif
