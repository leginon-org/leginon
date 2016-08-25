/*----------------------------------------------------------------------------*
*
*  tomopyemanmodule.c  -  eman wrapper library
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopy.h"
#include "tomopyeman.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TomoPyEmanExceptions[ E_TOMOPYEMAN_MAXCODE - E_TOMOPYEMAN ] = {
  { "E_TOMOPYEMAN",        "internal error ("TomoPyEmanName")" },
  { "E_TOMOPYEMAN_INIT",   "EMAN libraries could not be loaded" },
  { "E_TOMOPYEMAN_EMDATA", "not an EMData object" },
};


/* variables */

static TomoPyEmanFn TomoPyEmanFunctions = {
  TomoPyEmanNew,
  TomoPyEmanSet,
  TomoPyEmanGet,
};


/* module initialization/finalization */

static Status TomoPyEmanModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TomoPyEmanExceptions, E_TOMOPYEMAN, E_TOMOPYEMAN_MAXCODE );
  if ( exception( status ) ) return status;

  if ( data == NULL ) return pushexception( E_TOMOPYEMAN );
  *data = &TomoPyEmanFunctions;

  return E_NONE;

}


/* module descriptor */

const Module TomoPyEmanModule = {
  TomoPyEmanName,
  TomoPyEmanVers,
  TomoPyEmanCopy,
  COMPILE_DATE,
  TomoPyEmanModuleInit,
  NULL,
  NULL,
};
