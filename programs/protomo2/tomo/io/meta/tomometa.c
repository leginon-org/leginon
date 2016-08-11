/*----------------------------------------------------------------------------*
*
*  tomometa.c  -  series: tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomometacommon.h"
#include "exception.h"


/* functions */

extern Status TomometaSetCycle
              (Tomometa *meta,
               int cycle)

{
  Status status;

  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  if ( cycle < 0 ) return pushexception( E_ARGVAL );

  if ( meta->cycle < 0 ) return pushexception( E_TOMOMETA );

  I3io *handle = meta->handle;

  while ( meta->cycle > cycle ) {

    int cyc = meta->cycle - 1;
    status = I3ioWrite( handle, CYC, 0, sizeof(meta->cycle), &cyc );
    if ( pushexception( status ) ) return status;

    status = I3ioDealloc( handle, OFFS + meta->cycle * BLOCK + GLOBL );
    if ( pushexception( status ) ) return status;

    status = I3ioDealloc( handle, OFFS + meta->cycle * BLOCK + AXIS );
    if ( pushexception( status ) ) return status;

    status = I3ioDealloc( handle, OFFS + meta->cycle * BLOCK + ORIEN );
    if ( pushexception( status ) ) return status;

    status = I3ioDealloc( handle, OFFS + meta->cycle * BLOCK + GEOM );
    if ( pushexception( status ) ) return status;

    meta->cycle--;

  }

  status = I3ioFlush( handle );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}
