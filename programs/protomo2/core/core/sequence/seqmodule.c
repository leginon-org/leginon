/*----------------------------------------------------------------------------*
*
*  seqmodule.c  -  core: sequence generator
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "seq.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage SeqExceptions[ E_SEQ_MAXCODE - E_SEQ ] = {
  { "E_SEQ", "internal error ("SeqName")" },
};


/* module initialization/finalization */

static Status SeqModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( SeqExceptions, E_SEQ, E_SEQ_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module SeqModule = {
  SeqName,
  SeqVers,
  SeqCopy,
  COMPILE_DATE,
  SeqModuleInit,
  NULL,
  NULL,
};
