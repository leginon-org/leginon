/*----------------------------------------------------------------------------*
*
*  tomoseriesmodule.h  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoseriesmodule_h_
#define tomoseriesmodule_h_

#include "tomoseries.h"
#include "module.h"


/* dependencies */

#include "tomogeommodule.h"
#include "tomometamodule.h"
#include "tomodatamodule.h"
#include "tomoparamreadmodule.h"
#include "windowmodule.h"
#include "imagemodule.h"
#include "transfmodule.h"
#include "stringsmodule.h"
#include "matmodule.h"


/* module descriptor */

extern const Module TomoseriesModule;


/* construct linked list */

static ModuleListNode TomoseriesModuleListNode = { NULL, ModuleListPtr, &TomoseriesModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomoseriesModuleListNode)


#endif
