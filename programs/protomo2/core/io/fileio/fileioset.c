/*----------------------------------------------------------------------------*
*
*  fileioset.c  -  io: file i/o
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
#include <sys/stat.h>


/* functions */

extern Status FileioSetFileMode
              (const Fileio *fileio)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->filemode ) {
    if ( fchmod( fileio->filedscr, fileio->filemode ) ) {
      if ( ( errno != EBADF ) || chmod( fileio->path, fileio->filemode ) ) {
        return exception( E_ERRNO );
      }
    }
  }

  return E_NONE;

}


extern Status FileioSetMode
              (Fileio *fileio,
               IOMode mode)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( mode & IODel ) {
    if ( ~fileio->mode & IOWr ) {
      return exception( E_FILEIO_DEL );
    }
    fileio->mode |= IODel;
  }

  if ( mode & IOFd ) fileio->mode |= IOFd;

  return E_NONE;

}


extern Status FileioClearMode
              (Fileio *fileio,
               IOMode mode)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( mode & IODel ) fileio->mode &= ~IODel;

  if ( mode & IOFd  ) fileio->mode &= ~IOFd;

  return E_NONE;

}
