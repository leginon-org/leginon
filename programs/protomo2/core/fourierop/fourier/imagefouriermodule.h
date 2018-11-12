/*----------------------------------------------------------------------------*
*
*  imagefouriermodule.h  -  fourierop: image transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagefouriermodule_h_
#define imagefouriermodule_h_

#include "imagefourier.h"
#include "module.h"


/* dependencies */

#include "fouriermodule.h"
#include "imagemodule.h"
#include "transfermodule.h"


/* module descriptor */

extern const Module ImageFourierModule;


/* construct linked list */

static ModuleListNode ImageFourierModuleListNode = { NULL, ModuleListPtr, &ImageFourierModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ImageFourierModuleListNode)


#endif
