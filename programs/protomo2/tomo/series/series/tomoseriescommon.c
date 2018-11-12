/*----------------------------------------------------------------------------*
*
*  tomoseriescommon.c  -  series: tomography
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
#include "io.h"
#include <stdlib.h>
#include <string.h>


extern char *TomoseriesPrfx
             (const TomoseriesParam *param,
              const char *metapath,
              const char *tiltpath)

{
  char *prfx;

  if ( param == NULL ) return NULL;

  if ( ( param->prfx != NULL ) && *param->prfx ) {
    prfx = strdup( param->prfx );
    return prfx;
  }

  if ( metapath != NULL ) {
    prfx = IOPathName( metapath );
    char *ptr = strchr( prfx, '.' );
    if ( ptr != NULL ) *ptr = 0;
    if ( *prfx ) return prfx;
    free( prfx );
  }

  if ( tiltpath != NULL ) {
    prfx = IOPathName( tiltpath );
    char *ptr = strchr( prfx, '.' );
    if ( ptr != NULL ) *ptr = 0;
    if ( *prfx ) return prfx;
    free( prfx );
  }

  return NULL;

}


extern char *TomoseriesOutPrfx
             (const char *prfx,
              const char *outdir)

{

  Size len = ( ( outdir == NULL ) || !*outdir ) ? 0 : strlen( outdir );
  char *ptr = malloc( len + 1 + strlen( prfx ) + 1 );
  if ( ptr == NULL ) return NULL;
  if ( len ) {
    strcpy( ptr, outdir );
    if ( ptr[len-1] != DIRSEP ) {
      ptr[len++] = DIRSEP;
    }
  }
  strcpy( ptr + len, prfx );

  return ptr;

}


extern char *TomoseriesCachePrfx
             (const char *prfx,
              const char *cacheprfx,
              const char *cachedir)

{

  if ( ( cacheprfx == NULL ) || !*cacheprfx ) cacheprfx = prfx;
  Size len = ( cachedir == NULL ) ? 0 : strlen( cachedir );
  char *ptr = malloc( len + 1 + strlen( cacheprfx ) + 1 );
  if ( ptr == NULL ) return NULL;
  if ( len ) {
    strcpy( ptr, cachedir );
    if ( ptr[len-1] != DIRSEP ) {
      ptr[len++] = DIRSEP;
    }
  }
  strcpy( ptr + len, cacheprfx );

  return ptr;

}
