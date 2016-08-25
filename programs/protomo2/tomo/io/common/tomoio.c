/*----------------------------------------------------------------------------*
*
*  tomoio.c  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoiocommon.h"
#include "imageioextra.h"
#include "array.h"
#include "heap.h"
#include "imageio.h"
#include "strings.h"
#include "baselib.h"
#include "exception.h"
#include "macros.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomoio *TomoioCreate
               (const char *path,
                const char *prfx,
                const Size count,
                const Image *image,
                const char *fmt)

{
  I3Image i3image;
  I3data *extra;
  Status status;

  if ( argcheck( image == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  if ( image->dim > 4 ) { pushexception( E_TOMOIO_DIM ); return NULL; }

  path = TomoioPath( path, prfx, ".img" );
  if ( path == NULL ) return NULL;

  Tomoio *tomoio = malloc( sizeof(*tomoio) );
  if ( tomoio == NULL ) { pushexception( E_MALLOC ); goto error1; }
  *tomoio = TomoioInitializer;

  status = I3dataGetImage( image, &i3image );
  if ( pushexception( status ) ) goto error2;
  if ( count ) i3image.len[3] = count;

  if ( fmt == NULL ) {


    status = pushexception( E_ARGVAL ); goto error2;

  } else {

    tomoio->mode = TomoioModeImageio;

    ImageioParam iopar = ImageioParamDefault;
    iopar.format = fmt;
    iopar.mode |= ImageioModeDel;

    Imageio *imageio = ImageioCreate( path, &i3image.image, &iopar );
    status = testcondition( imageio == NULL );
    if ( status ) goto error2;
    tomoio->handle.imageio = imageio;
    tomoio->iomode = ImageioGetMode( imageio );

    status = ImageioAddr( imageio, 0, i3image.size, &tomoio->addr );
    if ( exception( status ) ) goto error3;

    extra = &tomoio->extra;
    status = ImageioExtraSetup( imageio, tomoio->iomode, extra );
    if ( exception( status ) ) goto error3;

    if ( extra->init != NULL ) {
      status = extra->init( imageio, extra );
      if ( exception( status ) ) goto error3;
    }

    tomoio->metadata = malloc( sizeof(I3Image) );
    if ( tomoio->metadata == NULL ) { status = pushexception( E_MALLOC ); goto error3; }
    memcpy( tomoio->metadata, &i3image, sizeof(I3Image) );

  }

  if ( extra->handle == NULL ) { status = pushexception( E_TOMOIO_OP ); goto error3; }

  free( (char *)path );

  return tomoio;

  error3: TomoioClose( tomoio, status ); goto error1;
  error2: free( tomoio );
  error1: free( (char *)path );

  return NULL;

}


extern Tomoio *TomoioOpenReadOnly
               (const char *path,
                const char *prfx,
                Size *count,
                I3Image *image)

{
  I3Image buf, *i3image = &buf;
  I3data *extra;
  Status status;

  if ( argcheck( image == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  path = TomoioPath( path, prfx, ".img" );
  if ( path == NULL ) return NULL;

  Tomoio *tomoio = malloc( sizeof(*tomoio) );
  if ( tomoio == NULL ) { pushexception( E_MALLOC ); goto error1; }
  *tomoio = TomoioInitializer;

    tomoio->mode = TomoioModeImageio;

    Imageio *imageio = ImageioOpenReadOnly( path, &i3image->image, NULL );
    status = testcondition( imageio == NULL );
    if ( status ) goto error2;
    tomoio->handle.imageio = imageio;
    tomoio->iomode = ImageioGetMode( imageio );

    Size dim = i3image->image.dim;
    if ( !dim || ( dim > 4 ) || ( ( count == NULL ) && ( dim == 4 ) ) ) {
      status = pushexception( E_TOMOIO_DIM ); goto error3;
    }

    status = I3dataGetImage( &i3image->image, i3image );
    if ( pushexception( status ) ) goto error3;

    status = ImageioAddr( imageio, 0, i3image->size, &tomoio->addr );
    if ( exception( status ) ) goto error3;

    extra = &tomoio->extra;
    status = ImageioExtraSetup( imageio, tomoio->iomode, extra );
    if ( exception( status ) ) goto error3;

    if ( extra->init != NULL ) {
      status = extra->init( imageio, extra );
      if ( exception( status ) ) goto error3;
    }

    tomoio->metadata = malloc( sizeof(I3Image) );
    if ( tomoio->metadata == NULL ) { status = pushexception( E_MALLOC ); goto error3; }
    memcpy( tomoio->metadata, i3image, sizeof(I3Image) );

  if ( extra->handle == NULL ) { status = pushexception( E_TOMOIO_OP ); goto error3; }

  free( (char *)path );

  if ( count != NULL ) *count = i3image->len[3];

  if ( image != NULL ) *image = *i3image;

  return tomoio;

  error3: TomoioClose( tomoio, status ); goto error1;
  error2: free( tomoio );
  error1: free( (char *)path );

  return NULL;

}


extern Tomoio *TomoioSetAlloc
               (const Size count,
                const Image *image)

{
  I3Image i3image;
  Status status;

  if ( argcheck( image == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  if ( !image->dim || ( image->dim > 3 ) ) {
    pushexception( E_TOMOIO_DIM ); return NULL;
  }

  Tomoio *tomoio = malloc( sizeof(*tomoio) );
  if ( tomoio == NULL ) { pushexception( E_MALLOC ); return NULL; }
  *tomoio = TomoioInitializer;

  status = I3dataGetImage( image, &i3image );
  if ( pushexception( status ) ) goto error;

  uint8_t *addr = malloc( i3image.size * i3image.elsize );
  if ( addr == NULL ) { status = pushexception( E_MALLOC ); goto error; }

  tomoio->mode = TomoioModeMalloc;
  tomoio->handle.addr = addr;

  return tomoio;

  error: free( tomoio );

  return NULL;

}


extern Status TomoioClose
              (Tomoio *tomoio,
               Status fail)

{
  Status stat, status = E_NONE;

  if ( tomoio == NULL ) return exception( E_ARGVAL );

  if ( status ) fail = status;

  I3data *extra = &tomoio->extra;

  if ( !status ) {

    if ( tomoio->iomode & ( IONew | IOCre ) ) {

      if ( tomoio->sampling <= 0 ) status = exception( E_TOMOIO_REQ );

      if ( extra->writenew != NULL ) {
        status = extra->writenew( extra, I3dataSampling, 0, &tomoio->sampling );
        if ( status && ( status != E_I3DATA_IMPL ) ) fail = exception( status );
      }

    } else {

      if ( tomoio->sampling <= 0 ) fail = status = exception( E_TOMOIO );

    }

  }

  if ( extra->final != NULL ) {
    stat = extra->final( extra, fail );
    if ( exception( stat ) ) fail = status = stat;
  }

  switch ( tomoio->mode ) {

    case TomoioModeImageio: {
      Imageio *imageio = tomoio->handle.imageio;
      if ( !fail ) {
        stat = ImageioUndel( imageio );
        popexception( stat );
      }
      stat = ImageioClose( imageio );
      if ( exception( stat ) ) status = stat;
      if ( tomoio->metadata != NULL ) free( tomoio->metadata );
      break;
    }

    case TomoioModeMalloc: {
      if ( tomoio->handle.addr != NULL ) free( tomoio->handle.addr );
      break;
    }

    default: status = exception( E_TOMOIO );

  }

  free( tomoio );

  return status;

}
