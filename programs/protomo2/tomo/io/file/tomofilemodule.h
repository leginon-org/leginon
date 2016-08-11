/*----------------------------------------------------------------------------*
*
*  tomofilemodule.h  -  series: tilt series image file handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomofilemodule_h_
#define tomofilemodule_h_

#include "tomofile.h"
#include "module.h"


/* dependencies */

#include "tomotiltmodule.h"
#include "imageiomodule.h"
#include "stringsmodule.h"


/* module descriptor */

extern const Module TomofileModule;


/* construct linked list */

static ModuleListNode TomofileModuleListNode = { NULL, ModuleListPtr, &TomofileModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomofileModuleListNode)


#endif
