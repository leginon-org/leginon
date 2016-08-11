/*----------------------------------------------------------------------------*
*
*  imageioextramodule.h  -  imageioextra: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imageioextramodule_h_
#define imageioextramodule_h_

#include "imageioextra.h"
#include "module.h"


/* dependencies */

#include "imageiomodule.h"
#include "i3datamodule.h"


/* module descriptor */

extern const Module ImageioExtraModule;


/* construct linked list */

static ModuleListNode ImageioExtraModuleListNode = { NULL, ModuleListPtr, &ImageioExtraModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ImageioExtraModuleListNode)


#endif
