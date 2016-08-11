/*----------------------------------------------------------------------------*
*
*  imageiomodule.h  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imageiomodule_h_
#define imageiomodule_h_

#include "imageio.h"
#include "module.h"


/* dependencies */

#include "imageioextramodule.h"
#include "fileiomodule.h"
#include "imagemodule.h"
#include "stringparsemodule.h"
#include "stringformatmodule.h"

#include "fffiomodule.h"

#ifndef ENABLE_DYNAMIC
  #include "ccp4iomodule.h"
  #include "emiomodule.h"
  #include "imagiciomodule.h"
  #include "spideriomodule.h"
  #include "suprimiomodule.h"
  #include "tiffiomodule.h"
#endif


/* module descriptor */

extern const Module ImageioModule;


/* construct linked list */

static ModuleListNode ImageioModuleListNode = { NULL, ModuleListPtr, &ImageioModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ImageioModuleListNode)


#endif
