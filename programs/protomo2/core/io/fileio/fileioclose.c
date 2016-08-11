/*----------------------------------------------------------------------------*
*
*  fileioclose.c  -  io: file i/o
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
#include <sys/mman.h>


/* functions */

extern Status FileioClose
              (Fileio *fileio)

{
  Status status;

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->mode & IOFd ) {
    return E_NONE;
  }

  if ( fileio->mode & IODel ) {
    status = FileioUnlink( fileio );
    if ( exception( status ) ) return status;
  }

  if ( ~fileio->iostatus & FileioUln ) {
    status = FileioSetFileMode( fileio );
    if ( exception( status ) ) return status;
    status = FileioFlush( fileio );
    if ( exception( status ) ) return status;
  }

  if ( fileio->iostatus & FileioStdio ) {
    if ( fclose( fileio->stream ) ) {
      return exception( E_ERRNO );
    }
  } else {
    if ( fileio->iostatus & FileioMapio ) {
      if ( fileio->maplength ) {
        if ( munmap( fileio->mapaddr, fileio->maplength ) ) {
          return exception( E_ERRNO );
        }
      }
      fileio->iostatus &= ~FileioMapio;
    }
    if ( close( fileio->filedscr ) ) {
      return exception( E_ERRNO );
    }
  }

  FileioDestroy( fileio );

  return E_NONE;

}
