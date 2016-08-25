/*----------------------------------------------------------------------------*
*
*  tiffiomodule.h  -  imageio: TIFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tiffiomodule_h_
#define tiffiomodule_h_

#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module TiffioModule;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode TiffioModuleListNode = { NULL, ModuleListPtr, &TiffioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&TiffioModuleListNode)

#endif


#endif
