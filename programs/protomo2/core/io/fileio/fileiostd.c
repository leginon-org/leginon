/*----------------------------------------------------------------------------*
*
*  fileiostd.c  -  io: file i/o
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

extern Status FileioStd
              (Fileio *fileio)

{
  char mode[] = { 0, 0, 0 };

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }
  if ( fileio->iostatus & ( FileioStdio | FileioMapio ) ) {
    return exception( E_FILEIO_IOSET );
  }
  if ( fileio->mode & IOShr ) {
    return exception( E_FILEIO_MODE );
  }

  if ( fileio->mode & IOCre ) {
    mode[0] = 'w';
    mode[1] = '+';
  } else {
    mode[0] = 'r';
    if ( fileio->mode & IOWr ) mode[1] = '+';
  }

  fileio->stream = fdopen( fileio->filedscr, mode );
  if ( fileio->stream == NULL ) {
    return exception( E_ERRNO );
  }
  fileio->iostatus |= FileioStdio;

  return E_NONE;

}
