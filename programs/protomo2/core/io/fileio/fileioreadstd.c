/*----------------------------------------------------------------------------*
*
*  fileioreadstd.c  -  io: file i/o
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

extern Status FileioReadStd
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
  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }
  if ( ~fileio->iostatus & FileioStdio ) {
    return exception( E_FILEIO_OPEN );
  }
  if ( ~fileio->mode & IORd ) {
    return exception( E_FILEIO_PERM );
  }

  if ( fseeko( fileio->stream, offset, SEEK_SET ) ) {
    return exception( E_ERRNO );
  }

  if ( !length ) return E_NONE; /* seek without reading */

  Size rdcount = fread( addr, 1, length, fileio->stream );
  if ( rdcount == length ) {
    fileio->iostatus |= FileioRdio;
    return E_NONE;
  }

  if ( feof( fileio->stream ) ) return exception( E_EOF );
  if ( ferror( fileio->stream ) ) return exception( E_ERRNO );
  return exception( E_FILEIO_READ );

}
