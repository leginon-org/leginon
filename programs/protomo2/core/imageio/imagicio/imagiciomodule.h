/*----------------------------------------------------------------------------*
*
*  imagiciomodule.h  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagiciomodule_h_
#define imagiciomodule_h_

#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module ImagicioModule;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode ImagicioModuleListNode = { NULL, ModuleListPtr, &ImagicioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ImagicioModuleListNode)

#endif


#endif
