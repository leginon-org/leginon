/*----------------------------------------------------------------------------*
*
*  convolmodule.h  -  array: convolution type filters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef convolmodule_h_
#define convolmodule_h_

#include "convol.h"
#include "module.h"


/* dependencies */

#include "arraymodule.h"


/* module descriptor */

extern const Module ConvolModule;


/* construct linked list */

static ModuleListNode ConvolModuleListNode = { NULL, ModuleListPtr, &ConvolModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&ConvolModuleListNode)


#endif
