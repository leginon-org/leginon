/*----------------------------------------------------------------------------*
*
*  io.h  -  io: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef io_h_
#define io_h_

#include "iodefs.h"

#define IOName   "io"
#define IOVers   IOVERS"."IOBUILD
#define IOCopy   IOCOPY


/* exception codes */

enum {
  E_IO = IOModuleCode,
  E_IO_DIR,
  E_IO_MAXCODE
};


/* types */

typedef uint64_t IOIdent;


/* variables */

extern const char *IOTempDir;


/* prototypes */

extern char *IOCurrentPath
             (const char *path);

extern char *IOPathName
             (const char *path);

extern char *IOPathDir
             (const char *path);

extern char *IOPathTemp
             (const char *path);

extern char *IOPathList
             (const char **pathlist,
              const char *path);

extern Status IOCreateDir
              (const char *path);

extern IOIdent IOGetIdent
               (const char *str,
                IOIdent id0);


#endif
