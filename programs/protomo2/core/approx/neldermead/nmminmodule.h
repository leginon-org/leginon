/*----------------------------------------------------------------------------*
*
*  nmminmodule.h  -  fourier: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef nmminmodule_h_
#define nmminmodule_h_

#include "nmmin.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module NMminModule;


/* construct linked fourier */

static ModuleListNode NMminModuleListNode = { NULL, ModuleListPtr, &NMminModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&NMminModuleListNode)


#endif
