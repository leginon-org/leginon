/*----------------------------------------------------------------------------*
*
*  fileiocommon.h  -  io: file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fileiocommon_h_
#define fileiocommon_h_

#include "fileio.h"
#include <stdio.h>
#include <sys/types.h>


/* types */

typedef struct {
  mode_t mode;
  off_t  size;
  time_t atime;
  time_t mtime;
  time_t ctime;
} FileioStat;

typedef enum {
  FileioStdio = 0x001,
  FileioMapio = 0x002,
  FileioOpn   = 0x010,
  FileioUln   = 0x020,
  FileioErr   = 0x040,
  FileioRdio  = 0x100,
  FileioWrio  = 0x200,
  FileioModio = 0x400,
} FileioStatus;

struct _Fileio {
  const char *path;
  char *fullpath;
  mode_t filemode;
  int filedscr;
  FILE *stream;
  void *mapaddr;
  Size maplength;
  Offset mapoffset;
  Offset mapaddrbase;
  IOMode mode;
  FileioStat stat;
  FileioStatus iostatus;
};


/* prototypes */

extern Status FileioFileLock
              (int filedscr,
               Offset offset,
               Offset length,
               IOMode mode);


#endif
