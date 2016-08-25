/*----------------------------------------------------------------------------*
*
*  tomoseriesget.c  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseriescommon.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomogeom *TomoseriesGetGeom
                 (const Tomoseries *series)

{
  Bool full;
  Status status;

  if ( argcheck( series == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Size images = series->tilt->images;

  Tomogeom *geom = malloc( images * sizeof(Tomogeom) );
  if ( geom == NULL ) { pushexception( E_MALLOC ); return NULL; }

  memcpy( geom, series->geom, images * sizeof(Tomogeom) );

  for ( Size index = 0; index < series->tilt->images; index++ ) {

    Coord (*Ap)[2] = geom[index].Ap;
    Coord (*Aa)[2] = geom[index].Aa;

    status = TomometaGetTransf( series->meta, index, Aa, &full );
    if ( exception( status ) ) goto error;

    if ( !full ) {
      if ( !( ( ( Aa[0][0] == 0 ) && ( Aa[0][1] == 0 ) )
           || ( ( Aa[1][0] == 0 ) && ( Aa[1][1] += 0 ) ) ) ) {
        memcpy( Ap, Aa, sizeof(geom->Aa) );
        memset( Aa,  0, sizeof(geom->Aa) );
      }
    }

  }

  return geom;

  /* error handling */

  error: free( geom );

  return NULL;

}


extern Tomotilt *TomoseriesGetTilt
                 (const char *metapath,
                  const TomoseriesParam *param)

{
  Tomogeom geom;
  Bool full;
  Status status = E_NONE;

  char *prfx = TomoseriesPrfx( param, metapath, NULL );
  if ( prfx == NULL ) { pushexception( E_TOMOSERIES ); return NULL; }

  if ( param->flags & TomoLog ) {
    Message( "opening tilt series \"", prfx, "\"\n" );
  }

  Tomotilt *tilt;
  Tomometa *meta = TomometaOpen( metapath, prfx, &tilt, NULL, TomoReadonly );
  if ( testcondition( meta == NULL ) ) goto error1;

  for ( Size index = 0; index < tilt->images; index++ ) {

    status = TomogeomLoad( tilt, index, (void *)param->A, param->b, &geom );
    if ( exception( status ) ) goto error3;

    status = TomometaGetTransf( meta, index, geom.Aa, &full );
    if ( exception( status ) ) goto error3;

    status = TomogeomSave( geom.A, geom.Am, geom.Aa, geom.origin, full, index, tilt );
    if ( exception( status ) ) goto error3;

  }

  status = TomometaClose( meta, status );
  if ( exception( status ) ) goto error2;

  free( prfx );

  return tilt;

  /* error handling */

  error3: TomometaClose( meta, status );
  error2: TomotiltDestroy( tilt );
  error1: free( prfx );

  return NULL;

}
