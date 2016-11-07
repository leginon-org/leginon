/*----------------------------------------------------------------------------*
*
*  tomocache.c  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomocache.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* macros */

#define SAMP 0x0f
#define PROC 0xf0


/* variables */

static const char TomocacheIdent[8] = "TILT";


/* functions */

extern Tomocache *TomocacheCreate
                  (const char *path,
                   Size images,
                   Size sampling,
                   Tomoflags flags)

{
  Status status;

  if ( argcheck( path == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  if ( !images ) { pushexception( E_ARGVAL ); return NULL; }

  I3ioMeta samp = SAMP; samp &= sampling;
  if ( samp != sampling ) { pushexception( E_ARGVAL ); return NULL; }
  if ( !samp ) samp = 1;

  I3ioMeta preproc = ( flags & TomoPreproc ) ? PROC : 0;

  I3ioParam iopar = I3ioParamInitializer;
  iopar.initsegm = images;
  iopar.mode = IOBuf;

  I3io *handle = I3ioCreate( path, &iopar );
  if ( testcondition( handle == NULL ) ) return NULL;

  I3ioMeta meta = 0;
  strncpy( (char *)&meta, TomocacheIdent, sizeof(meta) );
  status = I3ioMetaSet( handle, 4, meta );
  if ( pushexception( status ) ) goto error1;

  status = I3ioMetaSet( handle, 5, 0 );
  if ( pushexception( status ) ) goto error1;

  status = I3ioMetaSet( handle, 6, sizeof(TomocacheDscr) );
  if ( pushexception( status ) ) goto error1;

  status = I3ioMetaSet( handle, 7, preproc | samp );
  if ( pushexception( status ) ) goto error1;

  TomocacheDscr *dscr = malloc( images * sizeof(TomocacheDscr) );
  if ( dscr == NULL ) { status = pushexception( E_MALLOC ); goto error1; }

  Tomocache *cache = malloc( sizeof(Tomocache) );
  if ( cache == NULL ) { status = pushexception( E_MALLOC ); goto error2; }

  cache->images = images;
  cache->handle = handle;
  cache->dscr = dscr;
  cache->sampling = sampling;
  cache->preproc = preproc ? True : False;
  cache->new = True;

  return cache;

  /* error handling */

  error2: free( dscr );
  error1: I3ioClose( handle, status );

  return NULL;

}


extern Tomocache *TomocacheOpen
                  (const char *path)

{
  Status status;

  if ( argcheck( path == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  I3ioParam *iopar = NULL;

  I3io *handle = I3ioOpenReadOnly( path, iopar );
  if ( testcondition( handle == NULL ) ) return NULL;

  I3ioMeta meta;
  status = I3ioMetaGet( handle, 4, &meta );
  if ( pushexception( status ) ) goto error1;
  if ( memcmp( &meta, TomocacheIdent, sizeof(meta) ) ) { pushexception( E_TOMOCACHE_FMT ); goto error1; }

  status = I3ioMetaGet( handle, 5, &meta );
  if ( pushexception( status ) ) goto error1;
  Size images = meta;
  if ( !images ) { status = pushexception( E_TOMOCACHE_FMT ); goto error1; }

  status = I3ioMetaGet( handle, 6, &meta );
  if ( pushexception( status ) ) goto error1;
  if ( meta != sizeof(TomocacheDscr) ) { status = pushexception( E_TOMOCACHE_FMT ); goto error1; }

  status = I3ioMetaGet( handle, 7, &meta );
  if ( pushexception( status ) ) goto error1;
  Bool preproc = ( meta & PROC ) ? True : False;
  Size sampling = meta & SAMP;
  if ( !sampling ) { status = pushexception( E_TOMOCACHE_FMT ); goto error1; }

  TomocacheDscr *dscr = I3ioReadBuf( handle, images, 0, images * sizeof(TomocacheDscr) );
  status = testcondition( dscr == NULL );
  if ( status ) goto error1;

  Tomocache *cache = malloc( sizeof(Tomocache) );
  if ( cache == NULL ) { status = pushexception( E_MALLOC ); goto error2; }

  cache->images = images;
  cache->handle = handle;
  cache->dscr = dscr;
  cache->sampling = sampling;
  cache->preproc = preproc;
  cache->new = False;

  return cache;

  /* error handling */

  error2: free( dscr );
  error1: I3ioClose( handle, E_NONE );

  return NULL;

}


extern Status TomocacheDestroy
              (Tomocache *cache,
               Status fail)

{
  Status stat, status = E_NONE;

  if ( argcheck( cache == NULL ) ) return pushexception( E_ARGVAL );

  if ( !fail && cache->new ) {

    stat = I3ioAlloc( cache->handle, cache->images, cache->images * sizeof(TomocacheDscr), 0 );
    if ( pushexception( stat ) ) { status = fail = stat; goto exit; }

    stat = I3ioWrite( cache->handle, cache->images, 0, cache->images * sizeof(TomocacheDscr), cache->dscr );
    if ( pushexception( stat ) ) { status = fail = stat; goto exit; }

    stat = I3ioMetaSet( cache->handle, 5, cache->images );
    if ( pushexception( stat ) ) { status = fail = stat; goto exit; }

  }

  exit:

  if ( cache->dscr != NULL ) free( cache->dscr );

  if ( cache->handle != NULL ) {

    stat = I3ioClose( cache->handle, fail );
    if ( exception( stat ) ) status = stat;

  }

  free( cache );

  return status;

}
