/*----------------------------------------------------------------------------*
*
*  tomoaligntilt.c  -  align: series alignment
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

extern Tomotilt *TomoalignTilt
                 (const Tomoalign *align)

{
  Status status;

  if ( argcheck( align  == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  if ( align->window == NULL ) { pushexception( E_TOMOALIGN ); return NULL; }
  if ( align->image == NULL ) { pushexception( E_TOMOALIGN ); return NULL; }
  if ( align->ref == NULL ) { pushexception( E_TOMOALIGN ); return NULL; }

  Tomotilt *tilt = TomotiltDup( align->series->tilt );
  status = testcondition( tilt == NULL );
  if ( status ) return NULL;

  TomotiltGeom *tiltgeom = tilt->tiltgeom;
  TomoimageList *list = align->image->list;

  for ( Size index = 0; index < align->series->tilt->images; index++, list++ ) {

    if ( list->flags & TomoimageDone ) {

      status = TomogeomSave( list->A, list->Am, list->Ap, list->origin, !!( list->flags & TomoimageFull ), index, tilt );
      if ( exception( status ) ) goto error;

    } else {

      tiltgeom[index].corr[0] =  tiltgeom[index].corr[1] = 0;

    }

  }

  return tilt;

  error: TomotiltDestroy( tilt );

  return NULL;

}
