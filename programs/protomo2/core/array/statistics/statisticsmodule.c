/*----------------------------------------------------------------------------*
*
*  statisticsmodule.c  -  array: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "statistics.h"
#include "exception.h"
#include "module.h"
#include "makedate.h"


/* exception messages */

static const ExceptionMessage StatisticsExceptions[ E_STATISTICS_MAXCODE - E_STATISTICS ] = {
  { "E_STATISTICS",          "internal error ("StatisticsName")" },
  { "E_STATISTICS_DATATYPE", "invalid data type for statistics"  },
};


/* module initialization/finalization */

static Status StatisticsModuleInit
              (void **data)

{
  Status status;

  status = ExceptionRegister( StatisticsExceptions, E_STATISTICS, E_STATISTICS_MAXCODE );
  if ( exception( status ) ) return status;

  return E_NONE;

}


/* module descriptor */

const Module StatisticsModule = {
  StatisticsName,
  StatisticsVers,
  StatisticsCopy,
  COMPILE_DATE,
  StatisticsModuleInit,
  NULL,
  NULL,
};
