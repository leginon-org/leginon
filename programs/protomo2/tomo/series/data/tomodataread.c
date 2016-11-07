/*----------------------------------------------------------------------------*
*
*  tomodataread.c  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomodatacommon.h"
#include "exception.h"


/* functions */

extern void *TomodataBeginRead
             (const Tomocache *cache,
              const TomodataDscr *dscr,
              const Size index)

{
  void *addr;

  if ( argcheck( dscr == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Offset offs = dscr->offs;
  Size size = dscr->size;

  if ( dscr->handle == NULL ) {

    Size elsize = TypeGetSize( dscr->img.type );
    offs *= elsize;
    size *= elsize;

    addr = I3ioBeginRead( cache->handle, index, offs, size );
    testcondition( addr == NULL );

  } else {

    addr = ImageioBeginRead( dscr->handle, offs, size );
    testcondition( addr == NULL );

  }

  return addr;

}


extern Status TomodataEndRead
              (const Tomocache *cache,
               const TomodataDscr *dscr,
               const Size index,
               void *addr)

{
  Status status;

  if ( argcheck( dscr == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  Offset offs = dscr->offs;
  Size size = dscr->size;

  if ( dscr->handle == NULL ) {

    Size elsize = TypeGetSize( dscr->img.type );
    offs *= elsize;
    size *= elsize;

    status = I3ioEndRead( cache->handle, index, offs, size, addr );
    logexception( status );

  } else {

    status = ImageioEndRead( dscr->handle, offs, size, addr );
    logexception( status );

  }

  return status;

}
