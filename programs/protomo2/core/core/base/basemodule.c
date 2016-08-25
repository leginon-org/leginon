/*----------------------------------------------------------------------------*
*
*  basemodule.c  -  core: initialization
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "base.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"
#include <string.h>


/* exception messages */

static const ExceptionMessage BaseExceptions[ E_BASE_MAXCODE - E_BASE ] = {
  { "E_BASE",         "internal error ("BaseName")"       },
  { "E_INIT",         "initialization error"              },
  { "E_IMPL",         "unimplemented feature"             },
  { "E_FINAL",        "error while exiting"               },
  { "E_REGISTER",     "module registration failed"        },
  { "E_MODULE",       "module version mismatch"           },
  { "E_EXCEPT",       "unhandled exception"               },
  { "E_DUMMY",        "unreported exception"              },
  { "E_ARGVAL",       "invalid function argument"         },
  { "E_MALLOC",       "memory allocation error"           },
  { "E_INTOVFL",      "integer overflow"                  },
  { "E_FLTOVFL",      "floating point overflow"           },
  { "E_FLTUNFL",      "floating point underflow"          },
  { "E_SIGNAL",       "caught signal "                    },
  { "E_PATH",         "undefined or invalid library path" },
  { "E_ERRNO",        "errno error code"                  },
  { "E_EOF",          "end of file"                       },
  { "E_FILENOTFOUND", "file not found"                    },
  { "E_FILEEXISTS",   "file already exists"               },
  { "E_FILEISDIR",    "file is a directory"               },
  { "E_FILENODIR",    "path component is not a directory" },
  { "E_FILEACCESS",   "permission denied"                 },
  { "E_INTERNAL",     "internal error" /* user */         },
  { "E_USER",         "" /* user specified message */     },
  { "E_WARN",         "" /* user specified message */     },
  { "E_VAL",          "invalid value"                     },
};


/* module initialization/finalization */

static Status BaseModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( BaseExceptions, E_BASE, E_BASE_MAXCODE );
  if ( exception( status ) ) return status;

  /* deferred error check */
  status = CoreRegisterSetStatus( E_NONE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module BaseModule = {
  BaseName,
  BaseVers,
  BaseCopy,
  COMPILE_DATE,
  BaseModuleInit,
  NULL,
  NULL,
};
