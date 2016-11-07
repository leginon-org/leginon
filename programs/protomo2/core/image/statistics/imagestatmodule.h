/*----------------------------------------------------------------------------*
*
*  imagestatmodule.h  -  image: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagestatmodule_h_
#define imagestatmodule_h_

#include "imagestat.h"
#include "module.h"


/* dependencies */

#include "imagearraymodule.h"
#include "statisticsmodule.h"


/* module descriptor */

extern const Module ImageStatModule;


/* construct linked list */

static ModuleListNode ImageStatModuleListNode = { NULL, ModuleListPtr, &ImageStatModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ImageStatModuleListNode)


#endif
