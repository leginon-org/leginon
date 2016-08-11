/*----------------------------------------------------------------------------*
*
*  tomodatainit.c  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomodatacommon.h"
#include "io.h"
#include "strings.h"
#include "exception.h"
#include "message.h"
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>


/* functions */

extern Status TomodataDir
              (char *path)

{
  Status status = E_NONE;

  if ( path != NULL ) {
    char *sep = strrchr( path, DIRSEP );
    if ( sep != NULL ) {
      *sep = 0;
      status = IOCreateDir( path );
      if ( pushexception( status ) ) {
        appendexception( ", " );
        appendexception( path );
      }
      *sep = DIRSEP;
    }
  }

  return status;

}


static char *TomodataFilepath
            (const char *prfx,
             Size sampling,
             Tomoflags flags)

{
  char samp[64];

  const char *preproc = ( flags & TomoPreproc ) ? "_pre" : "";

  if ( sampling > 1 ) {
    sprintf( samp, "_smp%"SizeU, sampling );
  } else {
    *samp = 0;
  }

  const char *sffx = ".i3c";

  char *path = StringConcat( prfx, preproc, samp, sffx, NULL );
  if ( path == NULL ) {
    pushexception( E_MALLOC );
  } else if ( TomodataDir( path ) ) {
    free( path ); path = NULL;
  }

  return path;

}


static Status TomodataFileInit
              (Tomodata *data,
               const TomodataParam *param)

{
  Status status;

  TomofileParam fpar = TomofileParamInitializer;
  fpar.pathlist = param->pathlist;
  fpar.imgsffx = param->imgsffx;
  fpar.format = param->format;
  fpar.flags |= data->flags;

  if ( param->cap ) fpar.cap = param->cap;
  fpar.cap &= ~( ImageioCapLoad | ImageioCapAmap | ImageioCapStd );

  status = TomofileInit( data->file, &fpar );

  return status;

}


static int TomodataLock
           (const char *path)

{

  int fd = open( path, O_RDWR | O_CREAT, S_IRUSR | S_IWUSR );
  if ( fd < 0 ) goto error;

  if ( lockf( fd, F_LOCK, 0 ) ) goto error;

  return fd;

  error: pushexception( E_ERRNO );

  return -1;

}


static int TomodataUnlock
           (const char *path,
            int fd)

{

  if ( fd < 0 ) return 0;

  if ( close( fd ) ) goto error;

  if ( unlink( path ) ) { logexception( E_ERRNO ); }

  return 0;

  error: pushexception( E_ERRNO );

  return -1;

}


static Tomocache *TomodataPreprocCache
                  (Tomodata *data,
                   TomodataDscr *dscr,
                   const TomodataParam *param)

{
  Tomocache *cache = NULL;
  Status status;

  char *filepath = TomodataFilepath( param->cacheprfx, 1, data->flags );
  if ( filepath == NULL ) { pushexception( E_MALLOC ); return NULL; }

  char *lockpath = StringConcat( filepath, ".lock", NULL );
  if ( lockpath == NULL ) { pushexception( E_MALLOC ); goto error1; }

  int fd = TomodataLock( lockpath );
  if ( fd < 0 ) goto error2;

  if ( param->sampling > 1 ) {

    cache = TomocacheOpen( filepath );
    if ( testcondition( cache == NULL ) ) {
      ExceptionPop();
    } else {
      if ( ( cache->images != data->images ) || ( cache->sampling != 1 ) || !cache->preproc ) {
        status = TomocacheDestroy( cache, E_NONE );
        logexception( status );
        cache = NULL;
      }
    }

  }

  if ( cache == NULL ) {

    cache = TomocacheCreate( filepath, data->images, 1, data->flags );
    if ( testcondition( cache == NULL ) ) goto error3;

    status = TomodataPreproc( data, data->cache, dscr, cache );
    if ( exception( status ) ) goto error4;

    status = TomocacheDestroy( cache, E_NONE );
    if ( exception( status ) ) goto error3;

    cache = TomocacheOpen( filepath );
    if ( testcondition( cache == NULL ) ) goto error3;

  }

  if ( TomodataUnlock( lockpath, fd ) ) goto error5;

  free( lockpath );
  free( filepath );

  return cache;

  error5: fd = -1;
  error4: TomocacheDestroy( cache, status );
  error3: TomodataUnlock( lockpath, fd );
  error2: free( lockpath );
  error1: free( filepath );

  return NULL;

}


static Tomocache *TomodataSampleCache
                  (const char *path,
                   Tomodata *data,
                   TomodataDscr *dscr,
                   Tomocache *cache,
                   const TomodataParam *param)

{
  Status status;

  char *lockpath = StringConcat( path, ".lock", NULL );
  if ( lockpath == NULL ) { pushexception( E_MALLOC ); return NULL; }

  int fd = TomodataLock( lockpath );
  if ( fd < 0 ) goto error1;

  Tomocache *samp = TomocacheCreate( path, data->images, param->sampling, data->flags );
  if ( testcondition( samp == NULL ) ) goto error2;

  status = TomodataSample( data, cache, dscr, samp, param->sampling );
  if ( exception( status ) ) goto error3;

  status = TomocacheDestroy( samp, E_NONE );
  if ( exception( status ) ) goto error2;

  samp = TomocacheOpen( path );
  if ( testcondition( samp == NULL ) ) goto error2;

  if ( TomodataUnlock( lockpath, fd ) ) goto error4;

  free( lockpath );

  return samp;

  error4: fd = -1;
  error3: TomocacheDestroy( samp, status );
  error2: TomodataUnlock( lockpath, fd );
  error1: free( lockpath );

  return NULL;

}


extern Status TomodataInit
              (Tomodata *data,
               const TomodataParam *param)

{
  Status status;

  if ( argcheck( data == NULL ) ) return pushexception( E_ARGVAL );

  if ( ( param == NULL ) || ( param->cacheprfx == NULL ) || !*param->cacheprfx ) {
    return pushexception( E_ARGVAL );
  }

  data->preproc = NULL;
  data->flags &= ~( TomoflagMask | TomoflagCache | TomoPreproc );
  data->flags |= param->flags & ( TomoflagMask | TomoflagCache );

  if ( param->preproc != NULL ) {
    if ( param->preproc->main.flags ) {
      data->preproc = param->preproc;
      data->flags |= param->flags & TomoPreproc;
    } else if ( param->preproc->mask.flags ) {
      Message( "preprocessing skipped", NULL );
    }
  }

  if ( ( data->cache != NULL ) && ( data->cache->sampling == param->sampling ) ) {
    return E_NONE;
  }

  if ( ~data->flags & TomoflagCache ) {
    if ( ~data->file->flags & TomoflagFile ) {
      status = TomodataFileInit( data, param );
      if ( exception( status ) ) return status;
    }
  }

  char *filepath = TomodataFilepath( param->cacheprfx, param->sampling, data->flags );
  if ( filepath == NULL ) return pushexception( E_MALLOC );

  Tomocache *cache = TomocacheOpen( filepath );
  if ( testcondition( cache == NULL ) ) {
    ExceptionPop();
  } else {
    if ( ( cache->images != data->images ) || ( cache->sampling != param->sampling )
      || ( ( param->sampling > 1 ) && !( data->flags & TomoSmp ) )
      || (  cache->preproc && !( data->flags & TomoPreproc ) )
      || ( !cache->preproc &&  ( data->flags & TomoPreproc ) ) ) {
      status = TomocacheDestroy( cache, E_NONE );
      logexception( status );
      cache = NULL;
    }
  }

  TomodataDscr *dscr = TomodataDscrCreate( data );
  status = testcondition( dscr == NULL );
  if ( status ) goto error1;

  if ( cache == NULL ) {

    if ( ~data->file->flags & TomoflagFile ) {
      status = TomodataFileInit( data, param );
      if ( exception( status ) ) goto error2;
    }
    status = TomodataDscrFile( data, dscr );
    if ( exception( status ) ) goto error2;

  } else {

    if ( data->flags & TomoflagInit ) {
      status = TomodataDscrCheck( cache, data->dscr );
      if ( exception( status ) ) goto error2;
    }
    status = TomodataDscrCache( cache, dscr );
    if ( exception( status ) ) goto error2;

  }

  Tomocache *cachesamp = cache;

  if ( ( data->flags & TomoPreproc ) && ( cache == NULL ) ) {

    cache = TomodataPreprocCache( data, dscr, param );
    status = testcondition( cache == NULL );
    if ( status ) goto error2;

  }

  if ( ( param->flags & TomoSmp ) && ( param->sampling > 1 ) && ( cachesamp == NULL ) ) {

    cachesamp = TomodataSampleCache( filepath, data, dscr, cache, param );
    status = testcondition( cachesamp == NULL );
    if ( status ) goto error2;

    if ( cache != NULL ) {
      status = TomocacheDestroy( cache, E_NONE );
      if ( exception( status ) ) goto error3;
    }

    cache = cachesamp;

  }

  if ( cache != NULL ) {
    if ( data->cache != NULL ) {
      status = TomocacheDestroy( data->cache, E_NONE );
      if ( exception( status ) ) goto error4;
    }
    data->cache = cache;
  }

  if ( data->dscr != NULL ) free( data->dscr );
  data->dscr = dscr;
  data->sampling = param->sampling;
  data->flags |= TomoflagInit;

  exit: free( filepath );

  return status;

  /* error handling */

  error4: data->cache = NULL; goto error2;
  error3: TomocacheDestroy( cachesamp, status );
  error2: free( dscr );
  error1: if ( cache != NULL ) TomocacheDestroy( cache, status );
  goto exit;

}


extern Status TomodataFinal
              (Tomodata *data,
               Status fail)

{
  Status stat, status = E_NONE;

  if ( data->cache != NULL ) {
    stat = TomocacheDestroy( data->cache, fail );
    if ( exception( stat ) ) status = stat;
    data->cache = NULL;
  }

  if ( data->file != NULL ) {
    stat = TomofileFinal( data->file );
    if ( exception( stat ) ) status = stat;
  }

  data->sampling = 0;
  data->flags &= ~TomoflagMask;

  return status;

}
