/*----------------------------------------------------------------------------*
*
*  tomodatapreproc.c  -  series: image file i/o
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
#include "message.h"
#include "preproc.h"
#include "exception.h"
#include "signals.h"
#include <stdlib.h>
#include <string.h>


/* functions */

#define logbuflen 96

extern Status TomodataPreproc
              (const Tomodata *data,
               const Tomocache *datacache,
               TomodataDscr *datadscr,
               Tomocache *cache)

{
  void *srcaddr, *dstaddr;
  uint8_t *mskaddr = NULL;
  Size dstsize;
  Size index;
  Status status = E_NONE;

  TomocacheDscr *cachedscr = cache->dscr;
  TomodataDscr *dscr = datadscr;

  for ( index = 0; index < cache->images; index++, cachedscr++, dscr++ ) {

    if ( SignalInterrupt ) { status = pushexception( E_SIGNAL ); goto error1; }

    if ( dscr->sampling > 1 ) { status = pushexception( E_TOMODATA ); goto error1; }

    cachedscr->number = dscr->number;
    cachedscr->len[0] = dscr->len[0];
    cachedscr->len[1] = dscr->len[1];
    cachedscr->low[0] = dscr->low[0];
    cachedscr->low[1] = dscr->low[1];
    cachedscr->type = dscr->img.type;
    cachedscr->attr = dscr->img.attr;
    memcpy( cachedscr->checksum, dscr->checksum, sizeof(cachedscr->checksum) );

    dstsize = dscr->size * TypeGetSize( dscr->img.type );

    status = I3ioAlloc( cache->handle, index, dstsize, 0 );
    if ( pushexception( status ) ) goto error1;

    dstaddr = I3ioBeginWrite( cache->handle, index, 0, dstsize );
    status = testcondition( dstaddr == NULL );
    if ( status ) goto error1;

    srcaddr = TomodataBeginRead( datacache, dscr, index );
    status = testcondition( srcaddr == NULL );
    if ( status ) goto error2;

    status = TomodataPreprocImage( data, dscr, srcaddr, dstaddr, &mskaddr );
    if ( pushexception( status ) ) goto error3;

    status = TomodataEndRead( datacache, dscr, index, srcaddr );
    if ( exception( status ) ) goto error2;

    status = I3ioEndWrite( cache->handle, index, 0, dstsize, dstaddr );
    if ( exception( status ) ) goto error1;

    dscr->sampling = 1;

    dscr->handle = NULL;
    dscr->offs = 0;

    if ( ( data->flags & TomoLog ) || ( data->preproc->main.flags & PreprocLog ) ) {
      char logbuf[logbuflen];
      TomodataLogString( data, datadscr, index, logbuf, logbuflen );
      Message( logbuf, " preprocessing\n" );
    }

  }

  if ( mskaddr != NULL ) free( mskaddr );

  return status;

  error3: TomodataEndRead( datacache, dscr, index, srcaddr );
  error2: I3ioEndWrite( cache->handle, index, 0, dstsize, dstaddr );
  error1: if ( mskaddr != NULL ) free( mskaddr );

  return status;

}


extern Status TomodataPreprocImage
              (const Tomodata *data,
               const TomodataDscr *dscr,
               const void *srcaddr,
               void *dstaddr,
               uint8_t **mskaddr)

{
  Status status;

  Size border = data->preproc->border;
  Size statlen[2], statori[2], statsize = 1;
  for ( Size d = 0; d < 2; d++ ) {
    statori[d] = border;
    statlen[d] = ( dscr->len[d] > 2 * border ) ? dscr->len[d] - 2 * border : 0;
    statsize *= statlen[d];
  }

  if ( data->preproc->mask.flags & PreprocBin ) {

    uint8_t *ptr = realloc( *mskaddr, dscr->size * sizeof(*ptr) );
    if ( ptr == NULL ) return exception( E_MALLOC );
    *mskaddr = ptr;

    status = PreprocBinary( 2, dscr->img.type, dscr->len, srcaddr, statori, statlen, NULL, dscr->len, *mskaddr, &data->preproc->mask );
    if ( exception( status ) ) return status;

  }

  status = Preproc( 2, dscr->img.type, dscr->len, srcaddr, TypeUint8, *mskaddr, statori, statlen, dscr->img.type, NULL, dscr->len, dstaddr, &data->preproc->main );
  if ( exception( status ) ) return status;

  return E_NONE;

}
