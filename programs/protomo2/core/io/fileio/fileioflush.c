/*----------------------------------------------------------------------------*
*
*  fileioflush.c  -  io: file i/o
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
#include <sys/mman.h>
#include <unistd.h>


/* functions */

extern Status FileioFlush
              (Fileio *fileio)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->iostatus & FileioMapio ) {
    if ( msync( fileio->mapaddr, fileio->maplength, MS_SYNC ) ) {
      fileio->iostatus |= FileioErr;
      return exception( E_ERRNO );
    }
  } else {
    if ( fileio->iostatus & FileioStdio ) {
      if ( fflush( fileio->stream ) ) {
        fileio->iostatus |= FileioErr;
        return exception( E_ERRNO );
      }
    }
    if ( fsync( fileio->filedscr ) ) {
      fileio->iostatus |= FileioErr;
      return exception( E_ERRNO );
    }
  }

  fileio->iostatus &= ~FileioModio;

  return E_NONE;

}
