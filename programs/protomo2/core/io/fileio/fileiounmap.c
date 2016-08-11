/*----------------------------------------------------------------------------*
*
*  fileiounmap.c  -  io: file i/o
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


/* functions */

extern Status FileioUnmap
              (Fileio *fileio)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->iostatus & FileioMapio ) {
    if ( fileio->maplength ) {
      if ( munmap( fileio->mapaddr, fileio->maplength ) ) {
        return exception( E_ERRNO );
      }
    }
    fileio->mapaddr = NULL;
    fileio->maplength = 0;
    fileio->mapoffset = 0;
    fileio->mapaddrbase = 0;
    fileio->iostatus &= ~FileioModio;
  }

  return E_NONE;

}
