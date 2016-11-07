/*----------------------------------------------------------------------------*
*
*  tomoseriesmapmodule.h  -  series: maps
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoseriesmapmodule_h_
#define tomoseriesmapmodule_h_

#include "tomoseriesmap.h"
#include "module.h"


/* dependencies */

#include "tomoseriesmodule.h"
#include "tomomapmodule.h"
#include "tomoiomodule.h"


/* module descriptor */

extern const Module TomoseriesmapModule;


/* construct linked list */

static ModuleListNode TomoseriesmapModuleListNode = { NULL, ModuleListPtr, &TomoseriesmapModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomoseriesmapModuleListNode)


#endif
