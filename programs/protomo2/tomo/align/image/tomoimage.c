/*----------------------------------------------------------------------------*
*
*  tomoimage.c  -  align: image geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoimagecommon.h"
#include "mat3.h"
#include "baselib.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status TomoimageInitList
              (const Tomoseries *series,
               TomoimageList *list,
               const Size *selection,
               const Size *exclusion)

{
  Status status;

  const Tomotilt *tilt = series->tilt;
  const TomotiltImage *image = tilt->tiltimage;
  Tomogeom *geom = series->geom;

  for ( Size index = 0; index < tilt->images; index++, list++, geom++, image++ ) {

    memcpy( list->origin, geom->origin, sizeof(list->origin) );

    memcpy( list->A, geom->A, sizeof(list->A) );

    status = Mat3Inv( list->A, list->A1, NULL );
    if ( exception( status ) ) return status;

    memcpy( list->Am, geom->Am, sizeof(list->Am) );

    memcpy( list->Af, geom->Af, sizeof(list->Af) );

    status = TomoimageSet( list, geom->Ap, False );
    if ( exception( status ) ) return status;

    if ( SelectExclude( series->selection, series->exclusion, image->number ) ) {
      list->flags = TomoimageSel;
      if ( SelectExclude( selection, exclusion, image->number ) ) list->flags |= TomoimageAli;
    } else {
      list->flags = 0;
    }

  }

  return E_NONE;

}


extern Tomoimage *TomoimageCreate
                  (const Tomoseries *series,
                   const Size *selection,
                   const Size *exclusion,
                   Coord startangle)

{
  Status status;

  if ( argcheck( series == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomoimage *image = malloc( sizeof(Tomoimage) );
  if ( image == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *image = TomoimageInitializer;

  const Tomotilt *tilt = series->tilt;
  image->cooref = tilt->param.cooref;

  image->list = malloc( tilt->images * sizeof(TomoimageList) );
  if ( image->list == NULL ) { pushexception( E_MALLOC ); goto error1; }

  status = TomoimageInitList( series, image->list, selection, exclusion );
  if ( pushexception( status ) ) goto error2;

  image->list[image->cooref].flags = TomoimageSel;

  if ( startangle < 0 ) {
    status = TomoimageSortSeparate( tilt, image );
    if ( pushexception( status ) ) goto error2;
  } else {
    status = TomoimageSortSimultaneous( tilt, image, startangle );
    if ( pushexception( status ) ) goto error2;
  }

  return image;

  error2: free( image->list );
  error1: free( image );

  return NULL;

}


extern Status TomoimageDestroy
              (Tomoimage *image)

{

  if ( argcheck( image == NULL ) ) return pushexception( E_ARGVAL );

  if ( image->min != NULL ) free( image->min );

  if ( image->list != NULL ) free( image->list );

  free( image );

  return E_NONE;

}
