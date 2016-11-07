/*----------------------------------------------------------------------------*
*
*  fileioaccess.c  -  io: file i/o
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

extern Status FileioAccess
              (const Fileio *fileio,
               Offset *size,
               void **addr,
               Size *length,
               Offset *offset)

{
  Offset filesize = -1;
  char *mapaddr = NULL;
  Size maplen = 0;
  Offset mapoff = 0;

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( size != NULL ) {

    if ( fileio->stat.size < 0 ) {
      return exception( E_FILEIO );
    }

    filesize = fileio->stat.size;

  }

  if ( addr != NULL ) {

    if ( fileio->iostatus & FileioMapio ) {

      mapaddr = fileio->mapaddr;
      maplen = fileio->maplength;
      mapoff = fileio->mapoffset;

    }

  }

  if ( size != NULL ) *size = filesize;
  if ( addr != NULL ) *addr = mapaddr;
  if ( length != NULL ) *length = maplen;
  if ( offset != NULL ) *offset = mapoff;

  return E_NONE;

}
