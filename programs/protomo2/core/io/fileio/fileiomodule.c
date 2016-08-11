/*----------------------------------------------------------------------------*
*
*  fileiomodule.c  -  io: file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fileio.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage FileioExceptions[ E_FILEIO_MAXCODE - E_FILEIO ] = {
  { "E_FILEIO",        "internal error ("FileioName")"    },
  { "E_FILEIO_CREAT",  "invalid path for file creation"   },
  { "E_FILEIO_MODE",   "invalid file access mode"         },
  { "E_FILEIO_OPEN",   "file is not open"                 },
  { "E_FILEIO_USE",    "file is already in use"           },
  { "E_FILEIO_DEL",    "attempt to delete readlonly file" },
  { "E_FILEIO_IOSET",  "unable to set i/o mode"           },
  { "E_FILEIO_IOCHK",  "invalid i/o mode"                 },
  { "E_FILEIO_PERM",   "i/o operation not permitted"      },
  { "E_FILEIO_MMAP",   "memory mapping error"             },
  { "E_FILEIO_COUNT",  "invalid i/o count"                },
  { "E_FILEIO_SIZE",   "invalid resize request"           },
  { "E_FILEIO_READ",   "read error"                       },
  { "E_FILEIO_WRITE",  "write error"                      },
};


/* module initialization/finalization */

static Status FileioModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( FileioExceptions, E_FILEIO, E_FILEIO_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module FileioModule = {
  FileioName,
  FileioVers,
  FileioCopy,
  COMPILE_DATE,
  FileioModuleInit,
  NULL,
  NULL,
};
