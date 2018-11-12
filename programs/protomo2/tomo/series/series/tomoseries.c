/*----------------------------------------------------------------------------*
*
*  tomoseries.c  -  series: tomography
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
#include "tomoseriesset.h"
#include "heapproc.h"
#include "strings.h"
#include "exception.h"
#include "message.h"
#include "module.h"
#include <stdlib.h>
#include <string.h>


/* variables */

static const TomoseriesParam TomoseriesParamDefault = {
  NULL,
  NULL,
  NULL,
  { NULL, NULL, ".img", NULL, 0, NULL, 0, 0 },
  0,
  NULL,
  NULL,
  NULL,
  NULL,
  0,
};


/* functions */

static Status TomoseriesCleanup
              (Tomoseries *series)

{
  Status stat, status = E_NONE;

  if ( series->selection != NULL ) {
    free( series->selection ); series->selection = NULL;
  }

  if ( series->exclusion != NULL ) {
    free( series->exclusion ); series->exclusion = NULL;
  }

  if ( series->data != NULL ) {
    stat = TomodataFinal( series->data, series->fail );
    if ( exception( stat ) ) status = stat;
  }

  if ( series->meta != NULL ) {
    stat = TomometaClose( series->meta, series->fail ? series->fail : ( ( series->flags & TomoDelete ) ? E_HEAPPROC_DEL : E_NONE ) );
    if ( exception( stat ) ) status = stat;
    series->meta = NULL;
  }

  return status;

}


static Status TomoseriesAtExit
              (void *arg)

{

  return TomoseriesCleanup( arg );

}


static Tomoseries *TomoseriesAlloc
                   (const Size images,
                    const char *prfx,
                    const char *outdir,
                    const char *cacheprfx,
                    Tomoflags flags)

{

  Tomoseries *series = malloc( sizeof(Tomoseries) );
  if ( series == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *series = TomoseriesInitializer;

  series->outprfx = TomoseriesOutPrfx( prfx, outdir );
  if ( series->outprfx == NULL ) { pushexception( E_MALLOC ); goto error1; }

  series->geom = malloc( images * sizeof(Tomogeom) );
  if ( series->geom == NULL ) { pushexception( E_MALLOC ); goto error2; }

  series->prfx = prfx;
  series->cacheprfx = cacheprfx;
  series->flags = flags & TomoflagMask;
  series->fail = E_TOMOSERIES;
  series->self = series;

  series->final = CoreRegisterAtExit( TomoseriesName, TomoseriesVers, TomoseriesCopy, TomoseriesAtExit, series->self );
  if ( series->final == NULL ) { pushexception( E_TOMOSERIES ); goto error3; }

  return series;

  /* error handling */

  error3: free( series->geom );
  error2: free( (char *)series->outprfx );
  error1: free( series );

  return NULL;

}


static Tomoseries *TomoseriesSetup
                   (Tomotilt *tilt,
                    const char *prfx,
                    const char *metapath,
                    const TomoseriesParam *param)

{
  Status status;

  char *cacheprfx = TomoseriesCachePrfx( prfx,  param->data.cacheprfx, param->cachedir );
  if ( cacheprfx == NULL ) { pushexception( E_TOMOSERIES ); return NULL; }

  Tomofile *file = TomofileCreate( tilt );
  if ( testcondition( file == NULL ) ) goto error1;

  Tomoseries *series = TomoseriesAlloc( tilt->images, prfx, param->outdir, cacheprfx, param->flags );
  if ( testcondition( series == NULL ) ) goto error2;

  series->data = TomodataCreate( tilt, file );
  if ( testcondition( series->data == NULL ) ) goto error3;

  Tomometa *meta = TomometaCreate( metapath, prfx, tilt, param->flags | TomoNewonly );
  if ( testcondition( meta == NULL ) ) goto error4;

  TomodataParam datapar;
  status = TomoseriesSetParam( param, cacheprfx, &datapar, series );
  if ( exception( status ) ) goto error5;

  status = TomodataInit( series->data, &datapar );
  if ( exception( status ) ) goto error5;

  if ( param->A != NULL ) {
    memcpy( series->A, param->A, sizeof(series->A) );
  }
  if ( param->b != NULL ) {
    memcpy( series->b, param->b, sizeof(series->b) );
  }

  status = TomogeomInit( tilt, series->A, series->b, series->geom );
  if ( exception( status ) ) goto error5;

  status = TomometaWrite( meta, tilt, file );
  if ( exception( status ) ) goto error5;
  series->meta = meta;

  series->tilt = tilt;

  return series;

  /* error handling */

  error5: TomometaClose( meta, E_HEAPPROC_DEL );
  error4: file = NULL;
  error3: series->prfx = series->cacheprfx = NULL;
          TomoseriesDestroy( series );
  error2: if ( file != NULL ) TomofileDestroy( file );
  error1: free( cacheprfx );

  return NULL;

}


extern Tomoseries *TomoseriesCreate
                   (const Tomotilt *tilt,
                    const char *metapath,
                    const TomoseriesParam *param)

{

  if ( tilt == NULL ) { pushexception( E_ARGVAL ); return NULL; }

  if ( param == NULL ) param = &TomoseriesParamDefault;

  char *prfx = TomoseriesPrfx( param, metapath, NULL );
  if ( prfx == NULL ) { pushexception( E_TOMOSERIES ); return NULL; }

  if ( param->flags & TomoLog ) {
    Message( "creating tilt series \"", prfx, "\"\n" );
  }

  Tomotilt *tiltdup = TomotiltDup( tilt );
  if ( testcondition( tiltdup == NULL ) ) goto error1;

  Tomoseries *series = TomoseriesSetup( tiltdup, prfx, metapath, param );
  if ( testcondition( series == NULL ) ) goto error2;

  return series;

  /* error handling */

  error2: TomotiltDestroy( tiltdup );
  error1: free( prfx );
  return NULL;

}


extern Tomoseries *TomoseriesNew
                   (const char *tiltpath,
                    const char *metapath,
                    const TomoseriesParam *param)

{
  char *tpath = NULL;

  if ( param == NULL ) param = &TomoseriesParamDefault;

  char *prfx = TomoseriesPrfx( param, metapath, tiltpath );
  if ( prfx == NULL ) { pushexception( E_TOMOSERIES ); return NULL; }

  if ( param->flags & TomoLog ) {
    Message( "creating new tilt series \"", prfx, "\"\n" );
  }

  if ( ( tiltpath == NULL ) || !*tiltpath ) {
    tpath = StringConcat( prfx, ".tlt", NULL );
    if ( tpath == NULL ) { pushexception( E_MALLOC ); goto error1; }
    tiltpath = tpath;
  }

  Tomotilt *tilt = TomotiltRead( tiltpath );
  if ( testcondition( tilt == NULL ) ) goto error2;

  Tomoseries *series = TomoseriesSetup( tilt, prfx, metapath, param );
  if ( testcondition( series == NULL ) ) goto error3;

  if ( tpath != NULL ) free( tpath );

  return series;

  /* error handling */

  error3: TomotiltDestroy( tilt );
  error2: if ( tpath != NULL ) free( tpath );
  error1: free( prfx );
  return NULL;

}


extern Tomoseries *TomoseriesOpen
                   (const char *metapath,
                    const TomoseriesParam *param)

{
  Status status;

  if ( param == NULL ) param = &TomoseriesParamDefault;

  char *prfx = TomoseriesPrfx( param, metapath, NULL );
  if ( prfx == NULL ) { pushexception( E_TOMOSERIES ); return NULL; }

  if ( param->flags & TomoLog ) {
    Message( "opening tilt series \"", prfx, "\"\n" );
  }

  char *cacheprfx = TomoseriesCachePrfx( prfx,  param->data.cacheprfx, param->cachedir );
  if ( cacheprfx == NULL ) { pushexception( E_TOMOSERIES ); goto error1; }

  Tomotilt *tilt; Tomofile *file;
  Tomometa *meta = TomometaOpen( metapath, prfx, &tilt, &file, param->flags );
  if ( testcondition( meta == NULL ) ) goto error2;

  Tomodata *data = TomodataCreate( tilt, file );
  status = testcondition( data == NULL );
  if ( status ) goto error3;

  status = TomodataDscrFile( data, data->dscr );
  if ( exception( status ) ) goto error4;

  data->flags = TomoflagInit;

  Tomoseries *series = TomoseriesAlloc( tilt->images, prfx, param->outdir, cacheprfx, param->flags );
  if ( testcondition( series == NULL ) ) goto error4;

  TomodataParam datapar;
  status = TomoseriesSetParam( param, cacheprfx, &datapar, series );
  if ( exception( status ) ) goto error5;

  status = TomodataInit( data, &datapar );
  if ( exception( status ) ) goto error5;

  if ( param->A != NULL ) {
    memcpy( series->A, param->A, sizeof(series->A) );
  }
  if ( param->b != NULL ) {
    memcpy( series->b, param->b, sizeof(series->b) );
  }

  status = TomogeomInit( tilt, series->A, series->b, series->geom );
  if ( exception( status ) ) goto error5;

  for ( Size index = 0; index < tilt->images; index++ ) {
    status = TomometaGetTransf( meta, index, series->geom[index].Aa, NULL );
    if ( exception( status ) ) goto error5;
  }

  if ( param->flags & TomoLog ) {
    int cycle = TomometaGetCycle( meta );
    if ( cycle >= 0 ) {
      MessageFormat( "cycle %02d\n", cycle );
    }
  }

  series->tilt = tilt;
  series->data = data;
  series->meta = meta;

  return series;

  /* error handling */

  error5: series->prfx = series->cacheprfx = NULL;
          TomoseriesDestroy( series );
  error4: TomodataDestroy( data, E_TOMOSERIES );
  error3: TomometaClose( meta, E_TOMOSERIES );
          TomofileDestroy( file );
          TomotiltDestroy( tilt );
  error2: free( cacheprfx );
  error1: free( prfx );

  return NULL;

}


extern Status TomoseriesClose
              (Tomoseries *series)

{
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );

  series->fail = E_NONE;

  status = TomoseriesCleanup( series );
  logexception( status );

  return status;

}


extern Status TomoseriesDestroy
              (Tomoseries *series)

{
  Status stat, status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );

  status = TomoseriesCleanup( series );
  logexception( status );

  if ( series->data != NULL ) {
    stat = TomodataDestroy( series->data, series->fail );
    if ( exception( stat ) ) status = stat;
    series->data = NULL;
  }

  if ( series->tilt != NULL ) {
    stat = TomotiltDestroy( (Tomotilt *)series->tilt );
    if ( exception( stat ) ) status = stat;
    series->tilt = NULL;
  }

  free( (char *)series->cacheprfx ); series->cacheprfx = NULL;
  free( (char *)series->prfx ); series->prfx = NULL;
  free( series->geom ); series->geom = NULL;

  CoreUnregisterAtExit( series->final );

  free( series );

  return status;

}
