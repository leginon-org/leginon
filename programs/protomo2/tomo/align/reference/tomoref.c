/*----------------------------------------------------------------------------*
*
*  tomoref.c  -  align: reference
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoref.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomoref *TomorefCreate
                (const Tomoseries *series)

{

  if ( argcheck( series == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomoref *ref = malloc( sizeof(Tomoref) );
  if ( ref == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *ref = TomorefInitializer;

  Size images = series->tilt->images;

  TomorefImage *refimage = malloc( images * sizeof(TomorefImage) );
  if ( refimage == NULL ) { pushexception( E_MALLOC ); goto error; }
  ref->refimage = refimage;

  for ( Size index = 0; index < images; index++, refimage++ ) {
    refimage->transform = NULL;
    refimage->transfer = NULL;
  }

  ref->series = series;

  return ref;

  /* error handling */

  error: free( ref );

  return NULL;

}


extern Status TomorefDestroy
              (Tomoref *ref)

{
  Status status;

  if ( argcheck( ref == NULL ) ) return pushexception( E_ARGVAL );

  status = TomorefFinal( ref );
  logexception( status );

  Size images = ref->series->tilt->images;

  TomorefImage *refimage = ref->refimage;

  if ( refimage != NULL ) {
    for ( Size index = 0; index < images; index++, refimage++ ) {
      if ( refimage->transform != NULL ) free( refimage->transform );
      if ( refimage->transfer  != NULL ) free( refimage->transfer );
    }
    free( ref->refimage );
  }

  free( ref );

  return status;

}
