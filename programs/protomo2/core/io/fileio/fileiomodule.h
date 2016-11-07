/*----------------------------------------------------------------------------*
*
*  fileiomodule.h  -  io: file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fileiomodule_h_
#define fileiomodule_h_

#include "fileio.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"
#include "checksummodule.h"
#include "iomodule.h"


/* module descriptor */

extern const Module FileioModule;


/* construct linked list */

static ModuleListNode FileioModuleListNode = { NULL, ModuleListPtr, &FileioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&FileioModuleListNode)


#endif
