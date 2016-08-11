/*----------------------------------------------------------------------------*
*
*  tomofileinit.c  -  series: tilt series image file handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomofile.h"
#include "imageio.h"
#include "imageiochecksum.h"
#include "strings.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* variables */

static const TomofileParam TomofileParamDefault = {
  NULL,
  ".img",
  NULL,
  0,
  0
};


/* functions */

extern Status TomofileInit
              (Tomofile *tomofile,
               const TomofileParam *param)

{
  Status alloc = E_NONE;
  Status stat, status = E_NONE;

  if ( argcheck( tomofile == NULL ) ) return pushexception( E_ARGVAL );

  if ( tomofile->flags & TomoflagFile ) return pushexception( E_TOMOFILE );

  if ( !tomofile->files ) return E_NONE;

  if ( param == NULL ) param = &TomofileParamDefault;

  const char *sffx = param->imgsffx;
  if ( sffx == NULL ) sffx = TomofileParamDefault.imgsffx;

  tomofile->flags &= ~TomoflagMask;
  tomofile->flags |= param->flags & TomoflagMask;

  ImageioParam iopar = ImageioParamDefault;
  iopar.filepath = param->pathlist;
  if ( param->format != NULL ) iopar.format = param->format;
  if ( param->cap ) iopar.cap = param->cap;

  TomofileDscr *dscr = tomofile->dscr;
  TomofileIO *io = tomofile->io;

  for ( Size index = 0; index < tomofile->files; index++, dscr++, io++ ) {

    io->path = StringConcat( io->name, sffx, NULL );
    if ( io->path == NULL ) {
      if ( !alloc ) alloc = status = pushexception( E_MALLOC ); continue;
    }

    Image image;
    io->handle = ImageioOpenReadOnly( io->path, &image, &iopar );
    if ( io->handle == NULL ) {
      status = E_TOMOFILE_OPEN; continue;
    } else if ( dscr->dim != image.dim ) {
      status = pushexception( E_TOMOFILE_DIM ); goto looperr;
    }

    if ( tomofile->flags & TomoflagInit ) {

      for ( Size d = 0; d < dscr->dim; d++ ) {
        if ( dscr->len[d] != image.len[d] ) {
          status = pushexception( E_TOMOFILE_MOD ); goto looperr;
        }
      }
      if ( dscr->type != image.type ) { status = pushexception( E_TOMOFILE_MOD ); goto looperr; }
      if ( dscr->attr != image.attr ) { status = pushexception( E_TOMOFILE_MOD ); goto looperr; }
      TomofileDscr buf;
      stat = ImageioChecksum( io->handle, ChecksumTypeXor, sizeof(dscr->checksum), buf.checksum );
      if ( pushexception( stat ) ) { status = stat; goto looperr; }
      if ( memcmp( buf.checksum, dscr->checksum, sizeof(dscr->checksum) ) ) {
        status = pushexception( E_TOMOFILE_MOD ); goto looperr;
      }

    } else {

      for ( Size d = 0; d < dscr->dim; d++ ) {
        dscr->len[d] = image.len[d];
        dscr->low[d] = image.low[d];
      }
      dscr->type = image.type;
      dscr->attr = image.attr;
      stat = ImageioChecksum( io->handle, ChecksumTypeXor, sizeof(dscr->checksum), dscr->checksum );
      if ( pushexception( stat ) ) { status = stat; goto looperr; }

    }

    continue;

    looperr: ImageioErrPath( io->handle, status );

  }

  if ( status ) goto error;

  tomofile->flags |= TomoflagFile | TomoflagInit;

  return E_NONE;

  /* error handling */

  error: TomofileFinal( tomofile );

  return status;

}


extern Status TomofileFinal
              (Tomofile *tomofile)

{
  Status status = E_NONE;

  if ( argcheck( tomofile == NULL ) ) return exception( E_ARGVAL );

  TomofileIO *io = tomofile->io;
  if ( io != NULL ) {
    for ( Size index = 0; index < tomofile->files; index++, io++ ) {
      if ( io->handle != NULL ) {
        Status stat = ImageioClose( io->handle );
        if ( exception( stat ) ) if ( !status ) status = stat;
        io->handle = NULL;
      }
      if ( io->path != NULL ) {
        free( (char *)io->path );
        io->path = NULL;
      }
    }
  }

  tomofile->flags &= ~TomoflagFile;

  return status;

}
