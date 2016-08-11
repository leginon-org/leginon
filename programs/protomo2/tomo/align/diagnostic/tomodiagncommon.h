/*----------------------------------------------------------------------------*
*
*  tomodiagncommon.h  -  align: diagnostic output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomodiagncommon_h_
#define tomodiagncommon_h_

#include "tomodiagn.h"
#include "imageio.h"


/* types */

struct _Tomodiagn {
  Imageio *handle;
  Size size;
  Status status;
};


#endif
