/*----------------------------------------------------------------------------*
*
*  heapmodule.c  -  io: heap management
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "heap.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage HeapExceptions[ E_HEAP_MAXCODE - E_HEAP ] = {
  { "E_HEAP",       "internal error ("HeapName")"  },
  { "E_HEAP_INIT",  "initialization failure"       },
  { "E_HEAP_FIN",   "finalization failure"         },
  { "E_HEAP_USE",   "already in use"               },
  { "E_HEAP_META",  "metadata corruption"          },
  { "E_HEAP_FMT",   "invalid format"               },
  { "E_HEAP_SYN",   "metadata update failure"      },
  { "E_HEAP_ERR",   "corrupted data structure"     },
  { "E_HEAP_MOD",   "cannot modify data structure" },
  { "E_HEAP_WR",    "cannot write data"            },
  { "E_HEAP_DIR",   "segment directory too big"    },
  { "E_HEAP_SIZE",  "segment too big"              },
  { "E_HEAP_SEGM",  "segment not found"            },
  { "E_HEAP_EXIST", "segment already exists"       },
};


/* module initialization/finalization */

static Status HeapModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( HeapExceptions, E_HEAP, E_HEAP_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module HeapModule = {
  HeapName,
  HeapVers,
  HeapCopy,
  COMPILE_DATE,
  HeapModuleInit,
  NULL,
  NULL,
};
