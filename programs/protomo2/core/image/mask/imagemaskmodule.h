/*----------------------------------------------------------------------------*
*
*  imagemaskmodule.h  -  image: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagemaskmodule_h_
#define imagemaskmodule_h_

#include "imagemask.h"
#include "module.h"


/* dependencies */

#include "imagemodule.h"
#include "maskmodule.h"


/* module descriptor */

extern const Module ImageMaskModule;


/* construct linked list */

static ModuleListNode ImageMaskModuleListNode = { NULL, ModuleListPtr, &ImageMaskModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ImageMaskModuleListNode)


#endif
