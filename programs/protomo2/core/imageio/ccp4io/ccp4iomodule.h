/*----------------------------------------------------------------------------*
*
*  ccp4iomodule.h  -  imageio: CCP4 files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef ccp4iomodule_h_
#define ccp4iomodule_h_

#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module CCP4ioModule;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode CCP4ioModuleListNode = { NULL, ModuleListPtr, &CCP4ioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&CCP4ioModuleListNode)

#endif


#endif
