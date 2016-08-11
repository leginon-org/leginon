/*----------------------------------------------------------------------------*
*
*  checksummodule.h  -  core: checksums
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef checksummodule_h_
#define checksummodule_h_

#include "checksum.h"
#include "module.h"


/* dependencies */

/* none */


/* module descriptor */

extern const Module ChecksumModule;


/* construct linked list */

static ModuleListNode ChecksumModuleListNode = { NULL, ModuleListPtr, &ChecksumModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ChecksumModuleListNode)


#endif
