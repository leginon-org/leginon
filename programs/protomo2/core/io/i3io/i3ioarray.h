/*----------------------------------------------------------------------------*
*
*  i3ioarray.h  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef i3ioarray_h_
#define i3ioarray_h_

#include "i3io.h"


/* prototypes */

extern Status I3ioArrayAlloc
              (I3io *i3io,
               int segm,
               Size length,
               Size elsize);

extern Status I3ioArrayRead
              (I3io *i3io,
               int segm,
               Size offset,
               Size length,
               Size elsize,
               void *buf);

extern void *I3ioArrayReadBuf
             (I3io *i3io,
              int segm,
              Size offset,
              Size length,
              Size elsize);

extern Status I3ioArrayWrite
              (I3io *i3io,
               int segm,
               Size offset,
               Size length,
               Size elsize,
               const void *buf);

extern Status I3ioArrayWriteAlloc
              (I3io *i3io,
               int segm,
               Size length,
               Size elsize,
               const void *buf);


#endif
