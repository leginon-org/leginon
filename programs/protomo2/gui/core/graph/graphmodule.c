/*----------------------------------------------------------------------------*
*
*  graphmodule.c  -  graph: opengl graphics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "graph.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage GraphExceptions[ E_GRAPH_MAXCODE - E_GRAPH ] = {
  { "E_GRAPH",        "internal error ("GraphName")" },
  { "E_GRAPH_ENUM",   "invalid enum (GL error)"      },
  { "E_GRAPH_VAL",    "invalid value (GL error)"     },
  { "E_GRAPH_OP",     "invalid operation (GL error)" },
  { "E_GRAPH_OVFL",   "stack overflow (GL error)"    },
  { "E_GRAPH_UNFL",   "stack underflow (GL error)"   },
  { "E_GRAPH_MEM",    "out of memory (GL error)"     },
  { "E_GRAPH_TAB",    "table too large (GL error)"   },
  { "E_GRAPH_NOMSG",  "GL error"                     },
  { "E_GRAPH_VERS",   "invalid version"              },
};


/* module initialization/finalization */

static Status GraphModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( GraphExceptions, E_GRAPH, E_GRAPH_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module GraphModule = {
  GraphName,
  GraphVers,
  GraphCopy,
  COMPILE_DATE,
  GraphModuleInit,
  NULL,
  NULL,
};
