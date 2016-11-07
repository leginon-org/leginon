/*----------------------------------------------------------------------------*
*
*  transfermodule.h  -  array: pixel value transfer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef transfermodule_h_
#define transfermodule_h_

#include "transfer.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module TransferModule;


/* construct linked list */

static ModuleListNode TransferModuleListNode = { NULL, ModuleListPtr, &TransferModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TransferModuleListNode)


#endif
