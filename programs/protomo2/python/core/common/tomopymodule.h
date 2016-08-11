/*----------------------------------------------------------------------------*
*
*  tomopymodule.h  -  tomopy: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomopymodule_h_
#define tomopymodule_h_

#include "tomopy.h"
#include "module.h"


/* dependencies */

#include "tomoalignmodule.h"
#include "tomoseriesmapmodule.h"
#include "tomotiltfitmodule.h"
#include "imagearraymodule.h"
#include "imageiomodule.h"
#include "imagestatmodule.h"
#include "imagefouriermodule.h"


/* module descriptor */

extern const Module TomoPyModule;


/* construct linked list */

static ModuleListNode TomoPyModuleListNode = { NULL, ModuleListPtr, &TomoPyModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomoPyModuleListNode)


#endif
