/*----------------------------------------------------------------------------*
*
*  tomoaligndefs.h  -  definitions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoaligndefs_h_
#define tomoaligndefs_h_

#include "tomodefs.h"
#include "tomoalignconfig.h"


/* types */

typedef enum {
  TomoflagZeroRot   = 0x10000000,
  TomoflagEstimate  = 0x20000000,
  TomoflagAlignMask = 0x70000000,
} TomoflagsAlign;


#endif
