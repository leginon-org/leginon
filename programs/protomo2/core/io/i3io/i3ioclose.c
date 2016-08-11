/*----------------------------------------------------------------------------*
*
*  i3ioclose.c  -  io: i3 input/output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3iocommon.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status I3ioClose
              (I3io *i3io,
               Status fail)

{
  Status status;

  if ( i3io == NULL ) return exception( E_ARGVAL );

  status = HeapFinal( (Heap *)i3io, fail );
  if ( exception( status ) ) return status;

  return E_NONE;

}
