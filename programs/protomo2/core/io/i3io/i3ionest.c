/*----------------------------------------------------------------------------*
*
*  i3ionest.c  -  io: i3 input/output
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
#include "heapproc.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

static I3io *I3ioNewNested
             (I3io *i3io,
              int segm,
              I3ioMeta meta,
              IOMode mode)

{
  Status status;

  if ( argcheck( i3io == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( segm < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }

  Heap *heap = (Heap *)i3io;

  HeapParam param = HeapParamInitializer;
  param.mode = mode & HeapGetMode( heap );

  Heap *new = HeapNestInit( heap, segm, meta, &param );
  status = testcondition( new == NULL );
  if ( status ) return NULL;

  return (I3io *)new;

}


extern I3io *I3ioCreateNested
             (I3io *i3io,
              int segm,
              I3ioMeta meta)

{

  return I3ioNewNested( i3io, segm, meta, IOCre | IOExt | IOMod | IOWr | IORd );

}


extern I3io *I3ioCreateOnlyNested
             (I3io *i3io,
              int segm,
              I3ioMeta meta)

{

  return I3ioNewNested( i3io, segm, meta, IONew | IOExt | IOMod | IOWr | IORd );

}


static I3io *I3ioOldNested
             (I3io *i3io,
              int segm,
              I3ioMeta *meta,
              IOMode mode)

{
  HeapMeta met;
  Status status;

  if ( argcheck( i3io == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( segm < 0 ) ) { pushexception( E_ARGVAL ); return NULL; }

  Heap *heap = (Heap *)i3io;

  status = HeapAccess( heap, segm, NULL, NULL, &met );
  if ( pushexception( status ) ) return NULL;

  HeapParam param = HeapParamInitializer;
  param.mode = mode & HeapGetMode( heap );

  Heap *old = HeapNestInit( heap, segm, 0, &param );
  status = testcondition( old == NULL );
  if ( status ) return NULL;

  if ( meta != NULL ) *meta = met;

  return (I3io *)old;

}


extern I3io *I3ioOpenReadOnlyNested
             (I3io *i3io,
              int segm,
              I3ioMeta *meta)

{

  return I3ioOldNested( i3io, segm, meta, IOOld | IORd );

}


extern I3io *I3ioOpenReadWriteNested
             (I3io *i3io,
              int segm,
              I3ioMeta *meta)

{

  return I3ioOldNested( i3io, segm, meta, IOOld | IOMod | IOWr | IORd );

}


extern I3io *I3ioOpenUpdateNested
             (I3io *i3io,
              int segm,
              I3ioMeta *meta)

{

  return I3ioOldNested( i3io, segm, meta, IOOld | IOExt | IOMod | IOWr | IORd );

}
