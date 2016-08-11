/*----------------------------------------------------------------------------*
*
*  seqmodule.h  -  core: sequence generator
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef seqmodule_h_
#define seqmodule_h_

#include "seq.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module SeqModule;


/* construct linked list */

static ModuleListNode SeqModuleListNode = { NULL, ModuleListPtr, &SeqModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&SeqModuleListNode)


#endif
