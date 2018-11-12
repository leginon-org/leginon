/*----------------------------------------------------------------------------*
*
*  fileiolock.c  -  io: file i/o
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
#include <fcntl.h>
#include <unistd.h>


/* functions */

extern Status FileioFileLock
              (int filedscr,
               Offset offset,
               Offset length,
               IOMode mode)

{
  struct flock lock;

  lock.l_type =  mode ? ( ( mode & IOWr ) ? F_WRLCK : F_RDLCK ) : F_UNLCK;
  lock.l_whence = SEEK_SET;
  lock.l_start = offset;
  lock.l_len = length;

  /* 1 writer, or many readers, no simultaneous readers and writers */
  if ( fcntl( filedscr, F_SETLK, &lock ) < 0 ) {
    return exception( ( errno == EAGAIN ) ? E_FILEIO_USE : E_ERRNO );
  }

  return E_NONE;

}


extern Status FileioReadLock
              (Fileio *fileio,
               Offset offset,
               Size length)

{
  Status status;

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->mode & IOShr ) {
    status = FileioFileLock( fileio->filedscr, offset, length, IORd );
    if ( exception( status ) ) return status;
  }

  return E_NONE;

}


extern Status FileioWriteLock
              (Fileio *fileio,
               Offset offset,
               Size length)

{
  Status status;

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->mode & IOShr ) {
    status = FileioFileLock( fileio->filedscr, offset, length, IOWr );
    if ( exception( status ) ) return status;
  }

  return E_NONE;

}


extern Status FileioUnlock
              (Fileio *fileio,
               Offset offset,
               Size length)

{
  Status status;

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->mode & IOShr ) {
    status = FileioFileLock( fileio->filedscr, offset, length, 0 );
    if ( exception( status ) ) return status;
  }

  return E_NONE;

}
