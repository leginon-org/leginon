/*----------------------------------------------------------------------------*
*
*  tomopyimagemodule.h  -  tomopy: image handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomopyimagemodule_h_
#define tomopyimagemodule_h_

#include "tomopyimage.h"
#include "module.h"


/* dependencies */

#include "tomopymodule.h"


/* module descriptor */

extern const Module TomoPyImageModule;


/* construct linked list */

static ModuleListNode TomoPyImageModuleListNode = { NULL, ModuleListPtr, &TomoPyImageModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomoPyImageModuleListNode)


#endif
