/*----------------------------------------------------------------------------*
*
*  guigtkdisplaymodule.h  -  guigtk: EM image viewer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef guigtkdisplaymodule_h_
#define guigtkdisplaymodule_h_

#include "guigtkdisplay.h"
#include "module.h"


/* dependencies */

#include "guigtkmodule.h"
#include "graphmodule.h"
#include "imagearraymodule.h"
#include "imageiomodule.h"
#include "statisticsmodule.h"
#include "stringsmodule.h"
#include "stringparsemodule.h"
#include "textiomodule.h"


/* module descriptor */

extern const Module GuigtkDisplayModule;


/* construct linked list */

static ModuleListNode GuigtkDisplayModuleListNode = { NULL, ModuleListPtr, &GuigtkDisplayModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&GuigtkDisplayModuleListNode)


#endif
