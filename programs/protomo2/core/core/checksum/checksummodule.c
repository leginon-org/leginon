/*----------------------------------------------------------------------------*
*
*  checksummodule.c  -  core: checksums
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "checksum.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ChecksumExceptions[ E_CHECKSUM_MAXCODE - E_CHECKSUM ] = {
  { "E_CHECKSUM", "internal error ("ChecksumName")" },
  { "E_CHECKSUM_TYPE", "invalid checksum type"      },
};


/* module initialization/finalization */

static Status ChecksumModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ChecksumExceptions, E_CHECKSUM, E_CHECKSUM_MAXCODE );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module ChecksumModule = {
  ChecksumName,
  ChecksumVers,
  ChecksumCopy,
  COMPILE_DATE,
  ChecksumModuleInit,
  NULL,
  NULL,
};
