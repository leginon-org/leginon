/*----------------------------------------------------------------------------*
*
*  gslfftmodule.h  -  gslfft: fast Fourier transforms with gsl
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef gslfftmodule_h_
#define gslfftmodule_h_

#include "gslfft.h"
#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module GSLfftModule;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode GSLfftModuleListNode = { NULL, ModuleListPtr, &GSLfftModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&GSLfftModuleListNode)

#endif

#endif
