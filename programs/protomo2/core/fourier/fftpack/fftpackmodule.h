/*----------------------------------------------------------------------------*
*
*  fftpackmodule.h  -  fftpack: fast Fourier transforms with fftpack
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fftpackmodule_h_
#define fftpackmodule_h_

#include "fftpack.h"
#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module FFTpackModule;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode FFTpackModuleListNode = { NULL, ModuleListPtr, &FFTpackModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&FFTpackModuleListNode)

#endif


#endif
