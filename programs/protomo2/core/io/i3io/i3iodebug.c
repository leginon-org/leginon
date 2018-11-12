/*----------------------------------------------------------------------------*
*
*  i3iodebug.c  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3iodebug.h"
#include "heapdebug.h"
#include "exception.h"


/* functions */

extern Status I3ioDump
              (I3io *i3io)

{
  Status status;

  if ( i3io == NULL ) return exception( E_ARGVAL );

  status = HeapDump( stderr, (Heap *)i3io );
  if ( exception( status ) ) return status;

  return E_NONE;

}
