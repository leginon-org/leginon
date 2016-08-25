/*----------------------------------------------------------------------------*
*
*  tomobackprojmodule.h  -  map: weighted backprojection
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomobackprojmodule_h_
#define tomobackprojmodule_h_

#include "tomobackproj.h"
#include "module.h"


/* dependencies */

#include "tomomapmodule.h"
#include "tomotransfermodule.h"
#include "fouriermodule.h"
#include "threadmodule.h"


/* module descriptor */

extern const Module TomobackprojModule;


/* construct linked list */

static ModuleListNode TomobackprojModuleListNode = { NULL, ModuleListPtr, &TomobackprojModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomobackprojModuleListNode)


#endif
