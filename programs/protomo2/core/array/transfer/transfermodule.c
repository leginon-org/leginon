/*----------------------------------------------------------------------------*
*
*  transfermodule.c  -  array: pixel value transfer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transfer.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage TransferExceptions[ E_TRANSFER_MAXCODE - E_TRANSFER ] = {
  { "E_TRANSFER",          "internal error ("TransferName")" },
  { "E_TRANSFER_DATATYPE", "invalid data type for transfer"  },
};


/* module initialization/finalization */

static Status TransferModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( TransferExceptions, E_TRANSFER, E_TRANSFER_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module TransferModule = {
  TransferName,
  TransferVers,
  TransferCopy,
  COMPILE_DATE,
  TransferModuleInit,
  NULL,
  NULL,
};
