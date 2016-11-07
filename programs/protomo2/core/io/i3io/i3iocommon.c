/*----------------------------------------------------------------------------*
*
*  i3iocommon.c  -  io: i3 input/output
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
#include "macros.h"


/* functions */

extern Status I3ioSet
              (I3io *i3io,
               int segm,
               Offset *offs,
               Size *size)

{
  Offset off, siz;
  Status status;

  if ( *size > (Size)OffsetMaxSize ) return exception( E_I3IO_LEN );

  status = HeapAccess( (Heap *)i3io, segm, &off, &siz, NULL );
  if ( exception( status ) ) return status;

  if ( !*size ) {
    if ( siz > OffsetMaxSize ) return exception( E_I3IO_LEN );
    *size = siz;
  }

  if ( OFFSETADDOVFL( *offs, (Offset)*size ) ) return exception( E_I3IO_LEN );
  Offset end = *offs + *size;

  if ( *offs >= siz ) return exception( E_I3IO_OFF );
  if ( end > siz ) return exception( E_I3IO_LEN );

  if ( OFFSETADDOVFL( *offs, off ) ) return exception( E_I3IO_LEN );
  *offs += off;

  return E_NONE;

}
