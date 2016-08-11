/*----------------------------------------------------------------------------*
*
*  tomomapmodule.h  -  map: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomomapmodule_h_
#define tomomapmodule_h_

#include "tomomap.h"
#include "module.h"


/* dependencies */

#include "tomobackprojmodule.h"
#include "tomoiomodule.h"


/* module descriptor */

extern const Module TomomapModule;


/* construct linked list */

static ModuleListNode TomomapModuleListNode = { NULL, ModuleListPtr, &TomomapModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TomomapModuleListNode)


#endif
