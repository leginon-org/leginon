/*----------------------------------------------------------------------------*
*
*  fileioread.c  -  io: file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fileiocommon.h"
#include "exception.h"
#include <unistd.h>


/* functions */

extern Status FileioRead
              (Fileio *fileio,
               Offset offset,
               Size length,
               void *addr)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );

  if ( offset < 0 ) {
    return exception( E_ARGVAL );
  }
  if ( length > SSIZE_MAX ) {
    return exception( E_FILEIO_COUNT );
  }
  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }
  if ( ~fileio->mode & IORd ) {
    return exception( E_FILEIO_PERM );
  }

  Offset rdoffs = lseek( fileio->filedscr, offset, SEEK_SET );
  if ( rdoffs != offset ) {
    return exception( E_ERRNO );
  }

  if ( !length ) return E_NONE; /* seek without reading */

  char *ptr = addr;

  do {

    ssize_t rdcount = read( fileio->filedscr, ptr, length );
    if ( rdcount == 0 ) return exception( E_EOF );
    if ( rdcount < 0 ) return exception( E_ERRNO );
    if ( (Size)rdcount > length ) return exception( E_FILEIO_READ );

    length -= rdcount;
    ptr += rdcount;

  } while ( length );

  fileio->iostatus |= FileioRdio;

  return E_NONE;

}
