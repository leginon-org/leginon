/*----------------------------------------------------------------------------*
*
*  fileio.c  -  io: file i/o
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
#include <stdlib.h>


/* functions */

extern Status FileioDestroy
              (Fileio *fileio)

{

  if ( fileio != NULL ) {

    if ( fileio->fullpath != NULL ) {
      free( (char *)fileio->fullpath );
    }

    if ( fileio->path != NULL ) {
      free( (char *)fileio->path );
    }

    free( fileio );

  }

  return E_NONE;

}
