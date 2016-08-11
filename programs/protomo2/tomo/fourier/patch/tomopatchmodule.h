/*----------------------------------------------------------------------------*
*
*  tomopatchmodule.h  -  fourier: patch
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomopatchmodule_h_
#define tomopatchmodule_h_

#include "tomopatch.h"
#include "module.h"


/* dependencies */

#include "tomoseriesmodule.h"
#include "imagearraymodule.h"
#include "windowfouriermodule.h"


/* module descriptor */

extern const Module TomopatchModule;


/* construct linked list */

static ModuleListNode TomopatchModuleListNode = { NULL, ModuleListPtr, &TomopatchModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomopatchModuleListNode)


#endif
