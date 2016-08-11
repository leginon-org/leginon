/*----------------------------------------------------------------------------*
*
*  fileiotruncate.c  -  io: file i/o
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

extern Status FileioTruncate
              (Fileio *fileio,
               Offset size)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( size < 0 ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( size >= fileio->stat.size ) return E_NONE;
  if ( size < 0 ) return E_NONE;

  if ( ~fileio->mode & IOMod ) {
    return exception( E_FILEIO_SIZE );
  }

  if ( fileio->iostatus & FileioStdio ) {
    /* do nothing for the time being */
  } else {
    if ( ftruncate( fileio->filedscr, size ) ) {
      return exception( E_ERRNO );
    }
  }
  fileio->stat.size = size;

  return E_NONE;

}
