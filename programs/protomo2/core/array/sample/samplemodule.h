/*----------------------------------------------------------------------------*
*
*  samplemodule.h  -  array: sampling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef samplemodule_h_
#define samplemodule_h_

#include "sample.h"
#include "module.h"


/* dependencies */

#include "statisticsmodule.h"
#include "transfermodule.h"


/* module descriptor */

extern const Module SampleModule;


/* construct linked list */

static ModuleListNode SampleModuleListNode = { NULL, ModuleListPtr, &SampleModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&SampleModuleListNode)


#endif
