/*----------------------------------------------------------------------------*
*
*  imagemodule.h  -  image: images
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagemodule_h_
#define imagemodule_h_

#include "image.h"
#include "module.h"


/* dependencies */

#include "arraymodule.h"


/* module descriptor */

extern const Module ImageModule;


/* construct linked list */

static ModuleListNode ImageModuleListNode = { NULL, ModuleListPtr, &ImageModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ImageModuleListNode)


#endif
