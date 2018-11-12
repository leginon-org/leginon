/*----------------------------------------------------------------------------*
*
*  protomomodule.c  -  python tomography extension
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "protomo.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage ProtomoExceptions[ E_PROTOMO_MAXCODE - E_PROTOMO ] = {
  { "E_PROTOMO",     "internal error ("ProtomoName")"   },
  { "E_PROTOMO_ALI", "series has not been aligned yet"  },
  { "E_PROTOMO_FIT", "geometry has not been fitted yet" },
  { "E_PROTOMO_IMG", "no aligned images found"          },
  { "E_PROTOMO_UPD", "series has not been updated yet"  },
};


/* module initialization/finalization */

static Status ProtomoModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( ProtomoExceptions, E_PROTOMO, E_PROTOMO_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module ProtomoModule = {
  ProtomoName,
  ProtomoVers,
  ProtomoCopy,
  COMPILE_DATE,
  ProtomoModuleInit,
  NULL,
  NULL,
};
