/*----------------------------------------------------------------------------*
*
*  matdefs.h  -  core: matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef matdefs_h_
#define matdefs_h_

#include "defs.h"

#define MatName   "mat"
#define MatVers   COREVERS"."COREBUILD
#define MatCopy   CORECOPY


/* exception codes */

enum {
  E_MAT = MatModuleCode,
  E_MATSING,
  E_MAT_MAXCODE
};


#endif
