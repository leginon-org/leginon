/*----------------------------------------------------------------------------*
*
*  tomomapmodule.c  -  map: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomomap.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomomapExceptions[ E_TOMOMAP_MAXCODE - E_TOMOMAP ] = {
  { "E_TOMOMAP",      "internal error ("TomomapName")" },
  { "E_TOMOMAP_SAMP", "invalid map sampling"           },
  { "E_TOMOMAP_TYPE", "invalid map type"               },
};


/* module initialization/finalization */

static Status TomomapModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomomapExceptions, E_TOMOMAP, E_TOMOMAP_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module TomomapModule = {
  TomomapName,
  TomomapVers,
  TomomapCopy,
  COMPILE_DATE,
  TomomapModuleInit,
  NULL,
  NULL,
};
