/*----------------------------------------------------------------------------*
*
*  fileioopen.c  -  io: file i/o
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
#include "io.h"
#include "exception.h"
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>


/* functions */

static Status FileioFilepathOpen
              (Fileio *fileio,
               const char *filepath,
               const char *path,
               int flags)

{

  while ( True ) {

    fileio->path = IOPathList( &filepath, path );
    if ( fileio->path == NULL ) return E_FILENOTFOUND;

    fileio->fullpath = IOCurrentPath( fileio->path );
    if ( fileio->fullpath == NULL ) return E_MALLOC;

    fileio->filedscr = open( fileio->fullpath, flags );
    if ( fileio->filedscr >= 0 ) return E_NONE;

    free( (char *)fileio->path ); fileio->path = NULL;
    free( (char *)fileio->fullpath ); fileio->fullpath = NULL;

    if ( errno == EACCES  ) continue;
    if ( errno == EISDIR  ) continue;
    if ( errno == ELOOP   ) continue;
    if ( errno == ENOENT  ) continue;
    if ( errno == ENOTDIR ) continue;
    break;

  }

  return E_ERRNO;

}


extern Fileio *FileioOpen
               (const char *path,
                const FileioParam *param)

{
  FileioParam fileioparam;
  const char *errpath = " for temporary file";
  char *inpath = NULL;
  mode_t modeini = 0;
  Status status;

  if ( param == NULL ) {
    fileioparam = FileioParamInitializer;
    fileioparam.mode = IORd;
  } else {
    fileioparam = *param;
  }

  if ( ( path == NULL ) || !*path ) {
    if ( param == NULL ) {
      fileioparam.mode |= IOTmp;
    } else {
      if ( ~fileioparam.mode & IOTmp ) {
        pushexception( E_FILEIO_MODE ); goto error1;
      }
    }
  }

  if ( fileioparam.mode & IOTmp ) {
    inpath = IOPathTemp( path );
  } else {
    inpath = strdup( path );
    errpath = path;
  }
  if ( inpath == NULL ) {
    pushexception( E_MALLOC ); goto error1;
  }

  if ( fileioparam.mode & IOTmp ) fileioparam.mode |= IONew;
  if ( fileioparam.mode & IONew ) fileioparam.mode |= IOCre;
  if ( fileioparam.mode & IOCre ) fileioparam.mode |= IOExt;
  if ( fileioparam.mode & IOExt ) fileioparam.mode |= IOMod;
  if ( fileioparam.mode & IOMod ) fileioparam.mode |= IOWr;
  if ( fileioparam.mode & IOXcl ) {
    fileioparam.mode |= IOShr;
    if ( fileioparam.mode & IOWr ) fileioparam.mode |= IOLck;
  }

  Fileio *fileio = malloc( sizeof(Fileio) );
  if ( fileio == NULL ) {
    pushexception( E_MALLOC ); goto error1;
  }
  memset( fileio, 0, sizeof(Fileio) );
  fileio->path = NULL;
  fileio->fullpath = NULL;
  fileio->stream = NULL;
  fileio->mapaddr = NULL;

  int flags = ( fileioparam.mode & IOWr ) ? O_RDWR : O_RDONLY;
  if ( fileioparam.mode & IOCre ) flags |= O_CREAT;
  if ( fileioparam.mode & IONew ) flags |= O_EXCL;

  if ( fileioparam.mode & IOCre ) {
    modeini = S_IRUSR | S_IWUSR;
    if ( ~fileioparam.mode & IOTmp ) {
      umask( fileio->filemode = umask(0) );
      fileio->filemode = ( ~fileio->filemode ) & ( S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH );
    }
  }

  if ( ( fileioparam.mode & IOCre ) || ( fileioparam.filepath == NULL ) ) {
    fileio->fullpath = IOCurrentPath( inpath );
    if ( fileio->fullpath == NULL ) {
      pushexception( E_MALLOC ); goto error2;
    }
    fileio->filedscr = open( fileio->fullpath, flags, modeini );
    if ( fileio->filedscr < 0 ) {
      status = ( ( flags & O_CREAT ) && ( errno == ENOENT ) ) ? E_FILEIO_CREAT : E_ERRNO;
      pushexception( status ); goto error3;
    }
    fileio->path = strdup( inpath );
    if ( fileio->path == NULL ) {
      pushexception( E_MALLOC ); goto error6;
    }
  } else {
    status = FileioFilepathOpen( fileio, fileioparam.filepath, inpath, flags );
    if ( status ) {
      pushexception( status ); goto error4;
    }
  }

  if ( fileioparam.mode & IOTmp ) {
    if ( unlink( fileio->fullpath ) ) {
      pushexception( E_ERRNO ); goto error5;
    }
    fileio->iostatus = FileioUln;
  }

  if ( modeini ) {
    if ( fchmod( fileio->filedscr, modeini ) ) {
      logexception( E_ERRNO );
    }
  }

  if ( ( ~fileioparam.mode & IOShr ) || ( fileioparam.mode & IOLck ) ) {
    /* 1 writer, or many readers, no simultaneous readers and writers */
    status = FileioFileLock( fileio->filedscr, 0, 0, fileioparam.mode | IORd );
    if ( pushexception( status ) ) goto error7;
  }

  struct stat st;
  if ( fstat( fileio->filedscr, &st ) ) {
    pushexception( E_ERRNO ); goto error7;
  }
  fileio->stat.mode = st.st_mode;
  fileio->stat.size = st.st_size;
  fileio->stat.atime = st.st_atime;
  fileio->stat.mtime = st.st_mtime;
  fileio->stat.ctime = st.st_ctime;

  if ( fileioparam.mode & IOCre ) {
    /* truncate in case of preexisting file */
    if ( ftruncate( fileio->filedscr, 0 ) ) {
      pushexception( E_ERRNO ); goto error6;
    }
    fileio->stat.size = 0;
  }

  free( inpath );

  fileio->mode = fileioparam.mode;
  fileio->iostatus |= FileioOpn;

  return fileio;

  error7:
  if ( ~fileioparam.mode & IOCre ) goto error5;

  error6:
  if ( ~fileio->iostatus & FileioUln ) {
    if ( unlink( fileio->fullpath ) ) {
      logexception( E_ERRNO );
    }
  }

  error5:
  if ( close( fileio->filedscr ) ) {
    logexception( E_ERRNO );
  }

  error4:
  if ( fileio->path != NULL ) free( (char *)fileio->path );

  error3:
  if ( fileio->fullpath != NULL ) free( (char *)fileio->fullpath );

  error2:
  free( fileio );

  error1:
  appendexception( ", " );
  appendexception( errpath );
  if ( inpath != NULL ) free( inpath );

  return NULL;

}
