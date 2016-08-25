/*----------------------------------------------------------------------------*
*
*  iodir.c  -  io: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "io.h"
#include "exception.h"
#include <dirent.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>


/* functions */

extern Status IOCreateDir
              (const char *path)

{
  Status status;

  if ( ( path == NULL ) || !*path ) {
    return E_NONE;
  }

  DIR *dir = opendir( path );
  if ( dir != NULL ) {
    closedir( dir );
    return E_NONE;
  }

  if ( errno == ENOENT ) {
    if ( mkdir( path, S_IRWXU | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH ) ) {
      status = exception( E_IO_DIR );
    } else {
      status = E_NONE;
    }
  } else {
    status = exception( E_ERRNO );
  }

  return status;

}
