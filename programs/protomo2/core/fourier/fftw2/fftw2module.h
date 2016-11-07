/*----------------------------------------------------------------------------*
*
*  fftw2module.h  -  fftw2: fast Fourier transforms with fftw version 2
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fftw2module_h_
#define fftw2module_h_

#include "fftw2.h"
#include "module.h"


/* dependencies */

#ifndef ENABLE_DYNAMIC
  #include "basemodule.h"
#endif


/* module descriptor */

extern const Module FFTW2Module;


#ifndef ENABLE_DYNAMIC

/* construct linked list */

static ModuleListNode FFTW2ModuleListNode = { NULL, ModuleListPtr, &FFTW2Module, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&FFTW2ModuleListNode)

#endif


#endif
