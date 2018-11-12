/*----------------------------------------------------------------------------*
*
*  i3iocommon.h  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef i3iocommon_h_
#define i3iocommon_h_

#include "i3io.h"
#include "heapcommon.h"


/* types */

struct _I3io {
  Heap heap;
};


/* prototypes */

extern Status I3ioSet
              (I3io *i3io,
               int segm,
               Offset *offs,
               Size *size);


#endif
