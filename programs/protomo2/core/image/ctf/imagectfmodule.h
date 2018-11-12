/*----------------------------------------------------------------------------*
*
*  imagectfmodule.h  -  image: contrast transfer function
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagectfmodule_h_
#define imagectfmodule_h_

#include "imagectf.h"
#include "module.h"


/* dependencies */

#include "imagemodule.h"


/* module descriptor */

extern const Module ImageCTFModule;


/* construct linked list */

static ModuleListNode ImageCTFModuleListNode = { NULL, ModuleListPtr, &ImageCTFModule };

#undef  ModuleListPtr
#define ModuleListPtr (&ImageCTFModuleListNode)


#endif
