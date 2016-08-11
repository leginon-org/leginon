/*----------------------------------------------------------------------------*
*
*  tomotiltfitmodule.h  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomotiltfitmodule_h_
#define tomotiltfitmodule_h_

#include "tomotiltfit.h"
#include "module.h"


/* dependencies */

#include "tomotiltmodule.h"
#include "tomogeommodule.h"
#include "stringparsemodule.h"


/* module descriptor */

extern const Module TomotiltFitModule;


/* construct linked list */

static ModuleListNode TomotiltFitModuleListNode = { NULL, ModuleListPtr, &TomotiltFitModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomotiltFitModuleListNode)


#endif
