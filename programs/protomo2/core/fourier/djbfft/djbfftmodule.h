/*----------------------------------------------------------------------------*
*
*  djbfftmodule.h  -  djbfft: fast Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef djbfftmodule_h_
#define djbfftmodule_h_

#include "djbfft.h"
#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module DJBfftModule;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode DJBfftModuleListNode = { NULL, ModuleListPtr, &DJBfftModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&DJBfftModuleListNode)

#endif


#endif
