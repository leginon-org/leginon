/*----------------------------------------------------------------------------*
*
*  fileiowritestd.c  -  io: file i/o
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


/* functions */

extern Status FileioWriteStd
              (Fileio *fileio,
               Offset offset,
               Size length,
               const void *addr)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );

  if ( offset < 0 ) {
    return exception(E_ARGVAL);
  }
  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }
  if ( ~fileio->iostatus & FileioStdio ) {
    return exception( E_FILEIO_OPEN );
  }
  if ( ~fileio->mode & IOWr ) {
    return exception( E_FILEIO_PERM );
  }

  if ( fseeko( fileio->stream, offset, SEEK_SET ) ) {
    return exception( E_ERRNO );
  }

  if ( !length ) return E_NONE; /* seek without writing */

  Size wrcount = fwrite( addr, 1, length, fileio->stream );
  if ( wrcount == length ) {
    fileio->iostatus |= FileioWrio;
    fileio->iostatus |= FileioModio;
    return E_NONE;
  }

  fileio->iostatus |= FileioErr;
  if ( ferror( fileio->stream ) ) return exception( E_ERRNO );
  return exception( E_FILEIO_WRITE );

}
