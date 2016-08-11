/*----------------------------------------------------------------------------*
*
*  statisticsmodule.h  -  array: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef statisticsmodule_h_
#define statisticsmodule_h_

#include "statistics.h"
#include "module.h"


/* dependencies */

#include "basemodule.h"


/* module descriptor */

extern const Module StatisticsModule;


/* construct linked list */

static ModuleListNode StatisticsModuleListNode = { NULL, ModuleListPtr, &StatisticsModule, NULL };

#undef  ModuleListPtr
#define ModuleListPtr (&StatisticsModuleListNode)


#endif
