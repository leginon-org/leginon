/*----------------------------------------------------------------------------*
*
*  fileioget.c  -  io: file i/o
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

extern const char *FileioGetPath
                   (const Fileio *fileio)

{
  const char *path;

  if ( fileio == NULL ) return NULL;

  if ( ~fileio->iostatus & FileioOpn ) return NULL;

  path = fileio->path;

  return path;

}


extern const char *FileioGetFullPath
                   (const Fileio *fileio)

{
  const char *path;

  if ( fileio == NULL ) return NULL;

  if ( ~fileio->iostatus & FileioOpn ) return NULL;

  path = fileio->fullpath;

  return path;

}


extern int FileioGetFd
           (const Fileio *fileio)

{
  int fd;

  if ( fileio == NULL ) return -1;

  if ( ~fileio->iostatus & FileioOpn ) return -1;

  fd = fileio->filedscr;

  return fd;

}


extern IOMode FileioGetMode
              (const Fileio *fileio)

{
  IOMode mode;

  if ( fileio == NULL ) return 0;

  if ( ~fileio->iostatus & FileioOpn ) return 0;

  mode = fileio->mode;

  return mode;

}


extern Offset FileioGetSize
              (const Fileio *fileio)

{
  Offset offs;

  if ( fileio == NULL ) return 0;

  if ( ~fileio->iostatus & FileioOpn ) return 0;

  offs = fileio->stat.size;

  return offs;

}


extern void *FileioGetAddr
             (const Fileio *fileio)

{
  char *addr;

  if ( fileio == NULL ) return NULL;

  if ( ~fileio->iostatus & FileioOpn ) return NULL;

  if ( ~fileio->iostatus & FileioMapio ) return NULL;

  if ( !fileio->maplength ) return NULL;

  addr = fileio->mapaddr;
  if ( addr == NULL ) return NULL;

  return addr + fileio->mapaddrbase;

}
