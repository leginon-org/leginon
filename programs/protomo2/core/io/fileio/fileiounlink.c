/*----------------------------------------------------------------------------*
*
*  fileiounlink.c  -  io: file i/o
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


/* functions */

extern Status FileioUnlink
              (Fileio *fileio)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->mode & IODel ) {
    if ( ~fileio->mode & IOWr ) {
      return exception( E_FILEIO_DEL );
    }
    if ( ~fileio->iostatus & FileioUln ) {
      if ( unlink( fileio->path ) ) {
        return exception( E_ERRNO );
      }
      fileio->iostatus |= FileioUln;
    }
  }

  return E_NONE;

}
