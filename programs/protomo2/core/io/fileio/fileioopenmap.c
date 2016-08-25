/*----------------------------------------------------------------------------*
*
*  fileioopenmap.c  -  io: file i/o
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

extern Fileio *FileioOpenMap
               (const char *path,
                const FileioParam *param)

{
  Status status;

  Fileio *fileio = FileioOpen( path, param );
  status = testcondition( fileio == NULL );
  if ( status ) return NULL;

  status = FileioMap( fileio, 0, fileio->stat.size );
  if ( pushexception( status ) ) {
    if ( fileio->mode & IOCre ) fileio->mode |= IODel;
    status = FileioClose( fileio );
    logexception( status );
    fileio = NULL;
  }

  return fileio;

}
