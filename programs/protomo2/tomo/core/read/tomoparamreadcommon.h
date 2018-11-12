/*----------------------------------------------------------------------------*
*
*  tomoparamreadcommon.h  -  core: retrieve parameters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoparamreadcommon_h_
#define tomoparamreadcommon_h_

#include "tomoparamread.h"


/* prototypes */

extern Status TomoparamReadRot
              (Tomoparam *tomoparam,
               const char *ident,
               Coord *rot,
               Size *dim);


#endif
