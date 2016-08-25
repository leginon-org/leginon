/*----------------------------------------------------------------------------*
*
*  preprocmodule.h  -  image: preprocessing
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef preprocmodule_h_
#define preprocmodule_h_

#include "preproc.h"
#include "module.h"


/* dependencies */

#include "arraymodule.h"
#include "statisticsmodule.h"
#include "transfermodule.h"
#include "convolmodule.h"
#include "maskmodule.h"
#include "spatialmodule.h"


/* module descriptor */

extern const Module PreprocModule;


/* construct linked list */

static ModuleListNode PreprocModuleListNode = { NULL, ModuleListPtr, &PreprocModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&PreprocModuleListNode)


#endif
