/*----------------------------------------------------------------------------*
*
*  tomoalignseries.c  -  align: series alignment
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

extern Tomoalign *TomoalignSeries
                  (Tomoseries *series,
                   const TomoalignParam *aliparam,
                   const TomowindowParam *winparam,
                   const TomorefParam *refparam)

{
  Status status;

  if ( argcheck( series == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( aliparam == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( winparam == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( refparam == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomoflags seriesflags = series->flags;

  TomoalignParam alipar = *aliparam;
  series->flags |= alipar.flags & TomoflagAlignMask;
  if ( seriesflags & TomoLog ) {
    series->flags &= ~TomoLog;
    alipar.flags |= TomoLog;
  }

  Tomoalign *align = TomoalignCreate( series );
  status = testcondition( align == NULL );
  if ( status ) goto error0;

  status = TomoalignInit( align, &alipar, winparam, refparam );
  if ( exception( status ) ) goto error1;

  status = TomoalignExec( align );
  if ( exception( status ) ) goto error1;

  series->flags = seriesflags;

  return align;

  error1: TomoalignDestroy( align );
  error0: series->flags = seriesflags;

  return NULL;

}
