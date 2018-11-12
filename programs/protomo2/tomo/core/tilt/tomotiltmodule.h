/*----------------------------------------------------------------------------*
*
*  tomotiltmodule.h  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomotiltmodule_h_
#define tomotiltmodule_h_

#include "tomotilt.h"
#include "module.h"


/* dependencies */

#include "parsemodule.h"
#include "matmodule.h"
#include "stringparsemodule.h"


/* module descriptor */

extern const Module TomotiltModule;


/* construct linked list */

static ModuleListNode TomotiltModuleListNode = { NULL, ModuleListPtr, &TomotiltModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr ( &TomotiltModuleListNode )


#endif
