/*----------------------------------------------------------------------------*
*
*  iodefs.h  -  definitions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef iodefs_h_
#define iodefs_h_

#include "defs.h"
#include "ioconfig.h"


/* platform dependent */

#define PATHSEP ':'


/* types */

typedef enum {
  IOOld = 0x0000,
  IONew = 0x0001,
  IOCre = 0x0002,
  IOTmp = 0x0004,
  IOFd  = 0x0008,
  IORd  = 0x0010,
  IOWr  = 0x0020,
  IOMod = 0x0040,
  IOExt = 0x0080,
  IOMmp = 0x0100,
  IOShr = 0x0200,
  IOXcl = 0x0400,
  IOLck = 0x0800,
  IOBuf = 0x1000,
  IODel = 0x2000,
} IOMode;


#endif
