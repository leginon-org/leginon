/*----------------------------------------------------------------------------*
*
*  tomoalign.c  -  align: series alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoalign.h"
#include "message.h"
#include "exception.h"
#include "module.h"
#include <stdlib.h>


/* functions */

static Status TomoalignCleanup
              (void *tomoalign)

{
  Tomoalign *align = tomoalign;
  Status stat, status = E_NONE;

  stat = TomoalignFinal( align );
  if ( exception( stat ) ) status = stat;

  return status;

}


extern Tomoalign *TomoalignCreate
                  (const Tomoseries *series)

{

  if ( argcheck( series == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomoalign *align = malloc( sizeof(Tomoalign) );
  if ( align == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *align = TomoalignInitializer;

  align->series = series;
  align->data = align;

  align->final = CoreRegisterAtExit( TomoalignName, TomoalignVers, TomoalignCopy, TomoalignCleanup, align->data );
  if ( align->final == NULL ) {
    pushexception( E_TOMOALIGN );
    free( align );
    return NULL;
  }

  return align;

}


extern Status TomoalignDestroy
              (Tomoalign *align)

{
  Status status;

  if ( argcheck( align == NULL ) ) return pushexception( E_ARGVAL );

  align->flags |= TomoflagFinal;

  status = TomoalignCleanup( align );
  logexception( status );

  CoreUnregisterAtExit( align->final );

  free( align );

  return status;

}
