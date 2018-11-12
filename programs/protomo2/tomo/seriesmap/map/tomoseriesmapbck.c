/*----------------------------------------------------------------------------*
*
*  tomoseriesmapbck.c  -  series: maps
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
#include "mat3.h"
#include "exception.h"
#include "message.h"
#include <string.h>


/* functions */

extern Status TomoseriesmapInitBck
              (Tomomap *map,
               const Tomoseries *series)

{
  Status status;

  TomomapMode mode = TomomapGetMode( map );
  if ( ( mode.type != TomomapBck ) && ( mode.type != TomomapBpr ) ) {
    return pushexception( E_ARGVAL );
  }

  Tomogeom *geom = series->geom;
  Tomotransfer *trans = TomobackprojGetTransfer( map );
  uint8_t *selected = TomomapGetSelected( map );

  for ( Size index = 0; index < series->tilt->images; index++, geom++ ) {

    if ( selected[index] ) {

      memcpy( trans->A, geom->A, sizeof(trans->A) );
      status = Mat3Inv( trans->A, trans->A1, NULL );
      if ( pushexception( status ) ) return status;

      trans++;

    }

  }

  if ( series->flags & TomoLog ) {
    Message( "computing weighted projections...", "\n" );
  }

  status = TomobackprojWeight( map, NULL );
  if ( exception( status ) ) return status;

  return E_NONE;

}
