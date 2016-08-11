/*----------------------------------------------------------------------------*
*
*  tomometamodule.h  -  series: tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomometamodule_h_
#define tomometamodule_h_

#include "tomometa.h"
#include "module.h"


/* dependencies */

#include "tomotiltmodule.h"
#include "tomofilemodule.h"
#include "i3iomodule.h"
#include "stringsmodule.h"


/* module descriptor */

extern const Module TomometaModule;


/* construct linked list */

static ModuleListNode TomometaModuleListNode = { NULL, ModuleListPtr, &TomometaModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomometaModuleListNode)


#endif
