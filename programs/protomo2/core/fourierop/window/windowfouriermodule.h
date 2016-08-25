/*----------------------------------------------------------------------------*
*
*  windowfouriermodule.h  -  window: image windows
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef windowfouriermodule_h_
#define windowfouriermodule_h_

#include "windowfourier.h"
#include "module.h"


/* dependencies */

#include "imagearraymodule.h"
#include "imagemaskmodule.h"
#include "fouriermodule.h"
#include "ccfmodule.h"
#include "spatialmodule.h"


/* module descriptor */

extern const Module WindowFourierModule;


/* construct linked list */

static ModuleListNode WindowFourierModuleListNode = { NULL, ModuleListPtr, &WindowFourierModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&WindowFourierModuleListNode)


#endif
