/*----------------------------------------------------------------------------*
*
*  tomoalignwrite.c  -  align: series alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoaligncommon.h"
#include "exception.h"


/* functions */

extern Status TomoalignWrite
              (const Tomoalign *align,
               FILE *stream)

{
  Status status, stat;

  if ( argcheck( align  == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( stream == NULL ) ) return pushexception( E_ARGVAL );

  Tomotilt *tilt = TomoalignTilt( align );
  status = testcondition( tilt == NULL );
  if ( status ) return status;

  status = TomotiltWrite( tilt, stream );
  pushexception( status );

  stat = TomotiltDestroy( tilt );
  if ( pushexception( stat ) ) if ( !status ) status = stat;

  return status;

}
