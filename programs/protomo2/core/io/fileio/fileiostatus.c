/*----------------------------------------------------------------------------*
*
*  fileiostatus.c  -  io: file i/o
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

extern Status FileioStatusStd
              (Fileio *fileio,
               Bool *flag)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( flag == NULL ) ) return exception( E_ARGVAL );

  *flag = False;

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->iostatus & FileioStdio ) {
    *flag = True;
  }

  return E_NONE;

}


extern Status FileioStatusMap
              (Fileio *fileio,
               Bool *flag)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( flag == NULL ) ) return exception( E_ARGVAL );

  *flag = False;

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->iostatus & FileioMapio ) {
    *flag = True;
  }

  return E_NONE;

}


extern Status FileioStatusMod
              (Fileio *fileio,
               Bool *flag)

{

  if ( argcheck( fileio == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( flag == NULL ) ) return exception( E_ARGVAL );

  *flag = False;

  if ( ~fileio->iostatus & FileioOpn ) {
    return exception( E_FILEIO_OPEN );
  }

  if ( fileio->iostatus & FileioModio ) {
    *flag = True;
  }

  return E_NONE;

}
