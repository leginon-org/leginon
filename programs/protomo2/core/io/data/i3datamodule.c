/*----------------------------------------------------------------------------*
*
*  i3datamodule.c  -  io: i3 data
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3data.h"
#include "statistics.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage I3dataExceptions[ E_I3DATA_MAXCODE - E_I3DATA ] = {
  { "E_I3DATA",       "internal error ("I3dataName")" },
  { "E_I3DATA_IMPL",  "unimplemented data type"       },
  { "E_I3DATA_ENT",   "data entry already exists"     },
  { "E_I3DATA_NOENT", "data entry does not exist"     },
};


/* variables */

static const I3dataDscr I3dataTable[] = {
  { I3dataSampling,  "sampling",        1,  1, sizeof(Real64),    1, sizeof(Coord),     I3dataFlagPrint | I3dataFlagCopy | I3dataFlagList },
  { I3dataBinning,   "binning",         1,  1, sizeof(uint32_t),  1, sizeof(Size),      I3dataFlagPrint | I3dataFlagCopy },
  { I3dataTransf,    "transformation",  0,  1, sizeof(Real64),    0, sizeof(Coord),     I3dataFlagPrint | I3dataFlagCopy },
  { I3dataStat,      "statistics",      1,  4, sizeof(Real64),    1, sizeof(Stat),      I3dataFlagPrint                  },
  { I3dataCenters,   "centers",         0,  1, sizeof(int32_t),   0, sizeof(Index),     I3dataFlagPrint                  },
  { I3dataCount,     "count",           1,  2, sizeof(uint64_t),  1, sizeof(I3Count),   I3dataFlagPrint | I3dataFlagData },
  { I3dataImage,     "image",           1, 11, sizeof(uint32_t),  1, sizeof(I3Image),   I3dataFlagPrint | I3dataFlagData },
  { I3dataWindow2,   "window2",         0,  7, sizeof(Real64),    0, sizeof(I3Window2), I3dataFlagPrint | I3dataFlagData },
  { I3dataWindow3,   "window3",         0, 13, sizeof(Real64),    0, sizeof(I3Window3), I3dataFlagPrint | I3dataFlagData },
  { I3dataAlign,     "alignment",       0,  2, sizeof(uint64_t),  0, sizeof(I3Align),   I3dataFlagPrint | I3dataFlagData },
  { I3dataMax,       NULL,              0,  0, 0,                 0, 0,                 0		                 }
};


/* module initialization/finalization */

static Status I3dataModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( I3dataExceptions, E_I3DATA, E_I3DATA_MAXCODE );
  if ( exception( status ) ) return status;

  status = I3dataRegister( I3dataTable );
  if ( exception( status ) ) return status;

  return status;

}


/* module descriptor */

const Module I3dataModule = {
  I3dataName,
  I3dataVers,
  I3dataCopy,
  COMPILE_DATE,
  I3dataModuleInit,
  NULL,
  NULL,
};
