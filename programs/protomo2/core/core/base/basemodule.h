/*----------------------------------------------------------------------------*
*
*  basemodule.h  -  core: initialization
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef basemodule_h_
#define basemodule_h_

#include "base.h"
#include "module.h"


/* dependencies */

/* none */


/* module descriptor */

extern const Module BaseModule;


/* construct linked list, this is the initial node */

static ModuleListNode BaseModuleListNode = { NULL, NULL, &BaseModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&BaseModuleListNode)


#endif
