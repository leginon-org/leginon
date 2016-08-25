/*----------------------------------------------------------------------------*
*
*  tomomap.c  -  map: common routines
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
#include "tomobackproj.h"
#include "strings.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomomap *TomomapCreate
                (const TomomapParam *param)

{
  Status status;

  if ( param == NULL ) { pushexception( E_ARGVAL ); return NULL; }
  if ( !param->count ) { pushexception( E_ARGVAL ); return NULL; }
  if ( param->sampling && ( param->sampling < 1 ) ) { pushexception( E_TOMOMAP_SAMP ); return NULL; }

  Tomomap *map = malloc( sizeof(Tomomap) );
  if ( map == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *map = TomomapInitializer;

  if ( param->prfx != NULL ) {
    map->prfx = strdup( param->prfx );
    if ( map->prfx == NULL ) { pushexception( E_MALLOC ); goto error1; }
  }

  map->count = param->count;
  map->sampling = param->sampling ? param->sampling : 1;
  map->mode = param->mode;
  map->diam[0] = param->diam[0];
  map->diam[1] = param->diam[1];
  map->apod[0] = param->apod[0];
  map->apod[1] = param->apod[1];
  map->flags = param->flags & ( TomoflagMask | TomoflagMaskWrt );
  if ( map->flags & TomoMsg ) map->flags |= TomoLog;

  map->proj = malloc( param->count * sizeof(Tomoproj) );
  if ( map->proj == NULL ) { pushexception( E_MALLOC ); goto error2; }

  memset( map->proj, 0, param->count * sizeof(Tomoproj) );
  for ( Size i = 0; i < param->count; i++ ) {
    map->proj[i].img = NULL;
  }

  switch ( param->mode.type ) {
    case TomomapBck:
    case TomomapBpr: status = TomobackprojInit( map ); break;
    default: status = pushexception( E_TOMOMAP_TYPE );
  }
  if ( status ) goto error3;

  return map;

  /* error handling */

  error3: free( map->proj );
  error2: if ( map->prfx != NULL ) free( (char *)map->prfx );
  error1: free( map );

  return NULL;

}


extern Status TomomapDestroy
              (Tomomap *map)

{
  Status status = E_NONE;

  if ( map != NULL ) {

    switch ( map->mode.type ) {
      case TomomapBck:
      case TomomapBpr: status = TomobackprojFinal( map ); break;
      default: status = exception( E_TOMOMAP );
    }

    if ( map->proj != NULL ) {
      for ( Size i = 0; i < map->count; i++ ) {
        if ( map->proj[i].img != NULL ) free( map->proj[i].img );
      }
    }

    if ( map->selected != NULL ) free( map->selected );

    if ( map->prfx != NULL ) free( (char *)map->prfx );

    free( map );

  }

  return status;

}


extern Tomoproj *TomomapGetProj
                 (Tomomap *map)

{

  if ( map == NULL ) return NULL;

  return map->proj;

}


extern TomomapMode TomomapGetMode
                   (Tomomap *map)

{

  if ( map == NULL ) return TomomapModeInitializer;

  return map->mode;

}


extern uint8_t *TomomapGetSelected
                (Tomomap *map)

{

  if ( map == NULL ) return NULL;

  return map->selected;

}


extern void TomomapSetCount
            (Tomomap *map,
             Size count)

{

  if ( map != NULL ) map->count = count;

}


extern void TomomapSetSelected
            (Tomomap *map,
             uint8_t *selected)

{

  if ( map != NULL ) map->selected = selected;

}
