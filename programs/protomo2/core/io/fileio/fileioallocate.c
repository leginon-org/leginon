/*----------------------------------------------------------------------------*
*
*  fileioallocate.c  -  io: file i/o
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

extern Status FileioAllocate
              (Fileio *fileio,
               Offset size)

{
  char dummy = 0;
  Status status = E_NONE;

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( size < 0 ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( !size ) return E_NONE;
  if ( size <= fileio->stat.size ) return E_NONE;

  if ( ~fileio->mode & IOExt ) {
    return exception( E_FILEIO_SIZE );
  }

  if ( fileio->iostatus & FileioStdio ) {
    status = FileioWriteStd( fileio, size - 1, 1, &dummy );
    if ( exception( status ) ) return status;
  } else {
    status = FileioWrite( fileio, size - 1, 1, &dummy );
    if ( exception( status ) ) return status;
  }
  fileio->stat.size = size;

  return E_NONE;

}
