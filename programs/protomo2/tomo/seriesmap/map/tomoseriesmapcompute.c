/*----------------------------------------------------------------------------*
*
*  tomoseriesmapcompute.c  -  series: maps
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseriesmapcommon.h"
#include "tomobackproj.h"
#include "tomoio.h"
#include "i3data.h"
#include "exception.h"
#include "message.h"


/* functions */

extern Real *TomoseriesmapMem
             (const Tomoseries *series,
              const TomoseriesmapParam *param)

{
  Real *addr = NULL;
  Status status;

  if ( argcheck( series == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( param == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomomap *map = TomoseriesmapCreate( series, param );
  status = testcondition( map == NULL );
  if ( status ) return NULL;

  Tomocomp *comp = TomocompBeginMem( map, param->len );
  status = testcondition( comp == NULL );
  if ( status ) goto exit;

  switch ( param->mode.type ) {

    case TomomapBck:
    case TomomapBpr: {
      status = TomobackprojSum( comp );
      logexception( status );
      break;
    }

    default: status = pushexception( E_TOMOMAP_TYPE );

  }

  addr = TomocompEndMem( comp, status );

  exit: TomomapDestroy( map );

  return addr;

}


extern Status TomoseriesmapFile
              (const char *path,
               const char *fmt,
               const Tomoseries *series,
               const TomoseriesmapParam *param)

{
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( param == NULL ) ) return pushexception( E_ARGVAL );

  if ( path == NULL ) path = "";

  Tomomap *map = TomoseriesmapCreate( series, param );
  status = testcondition( map == NULL );
  if ( status ) return status;

  Tomocomp *comp = TomocompBeginFile( path, fmt, map, param->len );
  status = testcondition( comp == NULL );
  if ( status ) goto exit;

  switch ( param->mode.type ) {

    case TomomapBck:
    case TomomapBpr: {
      status = TomobackprojSum( comp );
      logexception( status );
      break;
    }

    default: status = pushexception( E_TOMOMAP_TYPE );

  }

  status = TomocompEndFile( comp, status );
  logexception( status );

  exit:

  status = TomomapDestroy( map );
  logexception( status );

  return E_NONE;

}
