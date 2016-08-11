/*----------------------------------------------------------------------------*
*
*  tomodefs.h  -  definitions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomodefs_h_
#define tomodefs_h_

#include "defs.h"
#include "tomoconfig.h"


/* macros */

#define TomoVec2Undef  { CoordMax, CoordMax }

#define TomoVec3Undef  { CoordMax, CoordMax, CoordMax }

#define TomoMat2Undef  { TomoVec2Undef, TomoVec2Undef }

#define TomoMat3Undef  { TomoVec3Undef, TomoVec3Undef, TomoVec3Undef }


/* types */

typedef enum {
  TomoLog       = 0x01,
  TomoMsg       = 0x02,
  TomoSmp       = 0x10,
  TomoPreproc   = 0x20,
  TomoRestart   = 0x40,
  TomoCycle     = 0x80,
  TomoReadonly  = 0x100,
  TomoNewonly   = 0x200,
  TomoDelete    = 0x400,
  TomoDryrun    = 0x800,
  TomoflagMask  = 0xfff,
  TomoflagInit  = 0x1000,
  TomoflagFile  = 0x2000,
  TomoflagCache = 0x4000,
  TomoflagFinal = 0x8000,
  TomoflagMatch = 0x10000,
  TomoflagCorr  = 0x20000,
  TomoflagMask2 = 0xff000,
  TomoflagMaskWrt  = 0xff00000,
} Tomoflags;


#endif
