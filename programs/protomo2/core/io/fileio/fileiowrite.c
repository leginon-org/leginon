/*----------------------------------------------------------------------------*
*
*  fileiowrite.c  -  io: file i/o
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

extern Status FileioWrite
              (Fileio *fileio,
               Offset offset,
               Size length,
               const void *addr)

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
  if ( ~fileio->mode & IOWr ) {
    return exception( E_FILEIO_PERM );
  }

  Offset wroffs = lseek( fileio->filedscr, offset, SEEK_SET );
  if ( wroffs != offset ) {
    return exception( E_ERRNO );
  }

  if ( !length ) return E_NONE; /* seek without writing */

  const char *ptr = addr;

  do {

    ssize_t wrcount = write( fileio->filedscr, ptr, length );
    if ( wrcount == 0 ) return exception( E_FILEIO_WRITE );
    if ( ( wrcount < 0 ) || ( (Size)wrcount > length ) ) {
      fileio->iostatus |= FileioErr;
      return exception( E_ERRNO );
    }

    fileio->iostatus |= FileioWrio;
    fileio->iostatus |= FileioModio;

    length -= wrcount;
    ptr += wrcount;

  } while ( length );

  return E_NONE;

}
