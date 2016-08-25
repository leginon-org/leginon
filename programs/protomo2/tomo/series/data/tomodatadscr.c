/*----------------------------------------------------------------------------*
*
*  tomodatadscr.c  -  series: image file i/o
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
#include "transf2.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern TomodataDscr *TomodataDscrCreate
                     (const Tomodata *data)

{

  TomodataDscr *datadscr = malloc( data->images * sizeof(*datadscr) );
  if ( datadscr == NULL ) { pushexception( E_MALLOC ); return NULL; }
  memset( datadscr, 0, data->images * sizeof(TomodataDscr) );

  const TomotiltImage *image = data->image;
  TomodataDscr *dscr = datadscr;

  for ( Size index = 0; index < data->images; index++, dscr++, image++ ) {

    dscr->number = image->number;
    dscr->handle = NULL;
    dscr->img.dim = 2;
    dscr->img.len = dscr->len;
    dscr->img.low = dscr->low;

  }

  return datadscr;

}


extern Status TomodataDscrFile
              (const Tomodata *data,
               TomodataDscr *dscr)

{

  if ( argcheck( data == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dscr == NULL ) ) return pushexception( E_ARGVAL );

  if ( !data->file->files ) return pushexception( E_TOMODATA );
  if ( ~data->file->flags & TomoflagInit ) return pushexception( E_TOMODATA );

  const TomotiltImage *image = data->image;
  const TomofileDscr *filedscr = data->file->dscr;
  const TomofileIO *fileio = data->file->io;

  for ( Size index = 0; index < data->images; index++, dscr++, image++ ) {

    const TomofileDscr *fdscr = filedscr + image->fileindex;
    const TomofileIO *fio = fileio + image->fileindex;

    dscr->handle = fio->handle;
    dscr->img.type = fdscr->type;
    dscr->img.attr = fdscr->attr;
    dscr->len[0] = fdscr->len[0];
    dscr->len[1] = fdscr->len[1];
    dscr->low[0] = fdscr->low[0];
    dscr->low[1] = fdscr->low[1];
    dscr->size = fdscr->len[0] * fdscr->len[1];
    dscr->offs = 0;
    memcpy( dscr->checksum, fdscr->checksum, sizeof(dscr->checksum) );

    if ( fdscr->dim == 3 ) {
      Size offs = image->fileoffset - fdscr->low[2];
      if ( ( image->fileoffset < fdscr->low[2] ) || ( offs >= fdscr->len[2] ) ) {
        return pushexception( E_TOMODATA_INDX );
      }
      dscr->offs = offs;
      dscr->offs *= dscr->size;
    }

    dscr->sampling = 0;
    dscr->B1[0][0] = 1; dscr->B1[0][1] = 0;
    dscr->B1[1][0] = 0; dscr->B1[1][1] = 1;
    dscr->B1[2][0] = 0; dscr->B1[2][1] = 0;

  }

  return E_NONE;

}


extern Status TomodataDscrCache
              (const Tomocache *cache,
               TomodataDscr *dscr)

{
  Status status;

  if ( argcheck( cache == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dscr == NULL ) ) return pushexception( E_ARGVAL );

  Size sampling = cache->sampling;

  for ( Size index = 0; index < cache->images; index++, dscr++ ) {

    status = TomocacheGetImage( cache, index, dscr->number, &dscr->img );
    if ( exception( status ) ) return status;
    if ( dscr->img.dim != 2 ) return pushexception( E_TOMODATA_DIM );

    dscr->handle = NULL;
    dscr->size = dscr->len[0] * dscr->len[1];
    dscr->offs = 0;
    memcpy( dscr->checksum, cache->dscr[index].checksum, sizeof(dscr->checksum) );

    if ( sampling > 1 ) {

      dscr->sampling = sampling;
      dscr->B1[0][0] = sampling;     dscr->B1[0][1] = 0;
      dscr->B1[1][0] = 0;            dscr->B1[1][1] = sampling;
      dscr->B1[2][0] = dscr->low[0]; dscr->B1[2][1] = dscr->low[1];

      status = Transf2Inv( dscr->B1, dscr->B1, NULL );
      if ( status ) return pushexception( status );

      dscr->low[0] = 0;
      dscr->low[1] = 0;

    } else {

      dscr->sampling = 1;
      dscr->B1[0][0] = 1; dscr->B1[0][1] = 0;
      dscr->B1[1][0] = 0; dscr->B1[1][1] = 1;
      dscr->B1[2][0] = 0; dscr->B1[2][1] = 0;

    }

  }

  return E_NONE;

}


extern Status TomodataDscrCheck
              (const Tomocache *cache,
               const TomodataDscr *dscr)

{
  Size len[2]; Index low[2];
  Image img;
  Status status;

  if ( argcheck( cache == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dscr == NULL ) ) return pushexception( E_ARGVAL );

  Size sampling = cache->sampling;
  img.len = len; img.low = low;

  for ( Size index = 0; index < cache->images; index++, dscr++ ) {

    if ( dscr->sampling > 1 ) return pushexception( E_TOMODATA );

    status = TomocacheGetImage( cache, index, dscr->number, &img );
    if ( exception( status ) ) return status;
    if ( img.dim != 2 ) return pushexception( E_TOMODATA_DIM );

    if ( sampling > 1 ) {

      if ( dscr->img.len[0] / sampling != img.len[0] ) return pushexception( E_TOMODATA_MOD );
      if ( dscr->img.len[1] / sampling != img.len[1] ) return pushexception( E_TOMODATA_MOD );

    } else {

      if ( dscr->img.len[0] != img.len[0] ) return pushexception( E_TOMODATA_MOD );
      if ( dscr->img.len[1] != img.len[1] ) return pushexception( E_TOMODATA_MOD );

    }

    if ( dscr->img.low[0] != img.low[0] ) return pushexception( E_TOMODATA_MOD );
    if ( dscr->img.low[1] != img.low[1] ) return pushexception( E_TOMODATA_MOD );

    if ( dscr->img.type   != img.type )   return pushexception( E_TOMODATA_MOD );
    if ( dscr->img.attr   != img.attr )   return pushexception( E_TOMODATA_MOD );

    if ( memcmp( cache->dscr[index].checksum, dscr->checksum, sizeof(dscr->checksum) ) ) return pushexception( E_TOMODATA_MOD );

  }

  return E_NONE;

}
