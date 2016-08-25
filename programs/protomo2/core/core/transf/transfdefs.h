/*----------------------------------------------------------------------------*
*
*  transfdefs.h  - core: linear transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef transfdefs_h_
#define transfdefs_h_

#include "defs.h"

#define TransfName   "transf"
#define TransfVers   COREVERS"."COREBUILD
#define TransfCopy   CORECOPY


/* exception codes */

enum {
  E_TRANSF = MatModuleCode,
  E_TRANSF_SING,
  E_TRANSF_MAXCODE
};


#endif
