/*----------------------------------------------------------------------------*
*
*  tomodatamodule.h  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomodatamodule_h_
#define tomodatamodule_h_

#include "tomodata.h"
#include "module.h"


/* dependencies */

#include "tomocachemodule.h"
#include "tomofilemodule.h"
#include "preprocmodule.h"
#include "samplemodule.h"
#include "transfmodule.h"
#include "stringsmodule.h"
#include "stringformatmodule.h"


/* module descriptor */

extern const Module TomodataModule;


/* construct linked list */

static ModuleListNode TomodataModuleListNode = { NULL, ModuleListPtr, &TomodataModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomodataModuleListNode)


#endif
