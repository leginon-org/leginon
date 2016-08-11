/*----------------------------------------------------------------------------*
*
*  fouriermodule.h  -  fourier: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fouriermodule_h_
#define fouriermodule_h_

#include "fourier.h"
#include "module.h"


/* dependencies */

#ifdef ENABLE_DYNAMIC
  #include "basemodule.h"
#else
  #ifdef ENABLE_FFTPACK
    #include "fftpackmodule.h"
  #endif
  #ifdef ENABLE_FFTW2
    #include "fftw2module.h"
  #endif
  #ifdef ENABLE_GSLFFT
    #include "gslfftmodule.h"
  #endif
  #ifdef ENABLE_DJBFFT
    #include "djbfftmodule.h"
  #endif
#endif


/* module descriptor */

extern const Module FourierModule;


/* construct linked list */

static ModuleListNode FourierModuleListNode = { NULL, ModuleListPtr, &FourierModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&FourierModuleListNode)


#endif
