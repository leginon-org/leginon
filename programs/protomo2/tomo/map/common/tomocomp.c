/*----------------------------------------------------------------------------*
*
*  tomocomp.c  -  map: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomomapcommon.h"
#include "tomoio.h"
#include "i3data.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

static Tomocomp *TomocompCreate
                 (Tomomap *map,
                  const Size len[3])

{

  Tomocomp *comp = malloc( sizeof(Tomocomp) );
  if ( comp == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *comp = TomocompInitializer;

  comp->map = map;
  comp->image.dim = 3;
  comp->image.len = comp->len;
  comp->image.low = comp->low;
  comp->image.type = TypeReal;
  comp->image.attr = ImageRealspc;

  comp->len[0] = len[0];
  comp->len[1] = len[1];
  comp->len[2] = len[2];

  comp->low[0] = -(Index)( len[0] / 2 );
  comp->low[1] = -(Index)( len[1] / 2 );
  comp->low[2] = -(Index)( len[2] / 2 );

  return comp;

}


extern Tomocomp *TomocompBeginMem
                 (Tomomap *map,
                  const Size len[3])

{
  Size size;
  Status status;

  if ( argcheck( map == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( len == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomocomp *comp = TomocompCreate( map, len );
  status = testcondition( comp == NULL );
  if ( status ) return NULL;

  status = ArraySize( 3, len, sizeof(Real), &size );
  if ( pushexception( status ) ) goto error;

  comp->addr = malloc( size * sizeof(Real) );
  if ( comp->addr == NULL ) { pushexception( E_MALLOC ); goto error; }

  return comp;

  error: free( comp );

  return NULL;

}


extern Real *TomocompEndMem
             (Tomocomp *comp,
              Status fail)

{
  Real *addr;

  if ( fail ) {
    free( comp->addr );
    addr = NULL;
  } else {
    addr = comp->addr;
  }

  free( comp );

  return addr;

}


extern Tomocomp *TomocompBeginFile
                 (const char *path,
                  const char *fmt,
                  Tomomap *map,
                  const Size len[3])

{
  Status status;

  if ( argcheck( map == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( argcheck( len == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  Tomocomp *comp = TomocompCreate( map, len );
  status = testcondition( comp == NULL );
  if ( status ) return NULL;

  comp->handle = TomoioCreate( path, map->prfx, 0, &comp->image, fmt );
  status = testcondition( comp->handle == NULL );
  if ( status ) goto error1;

  status = TomoioExtraSetSampling( comp->handle, map->sampling );
  if ( pushexception( status ) ) goto error2;

  return comp;

  error2: TomoioClose( comp->handle, status );
  error1: free( comp );

  return NULL;

}


extern Status TomocompEndFile
              (Tomocomp *comp,
               Status fail)

{
  Status status;

  status = TomoioClose( comp->handle, fail );
  logexception( status );

  free( comp );

  return status;

}


extern const I3data *TomocompGetExtra
                     (Tomocomp *comp)

{

  return TomoioGetExtra( comp->handle );

}
