/*----------------------------------------------------------------------------*
*
*  tomodatasample.c  -  series: image file i/o
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
#include "sample.h"
#include "transf2.h"
#include "exception.h"
#include "signals.h"
#include <string.h>


/* functions */

#define logbuflen 96

extern Status TomodataSample
              (const Tomodata *data,
               const Tomocache *datacache,
               TomodataDscr *datadscr,
               Tomocache *cache,
               Size sampling)

{
  void *srcaddr, *dstaddr;
  Size dstsize;
  Size dstlen[2];
  Size index;
  Status status;

  Size smp[2] = { sampling, sampling };
  Size ori[2] = { 0, 0 };
  SampleParam param = SampleParamInitializer;
  param.flags = SampleConvol;

  TomocacheDscr *cachedscr = cache->dscr;
  TomodataDscr *dscr = datadscr;

  for ( index = 0; index < cache->images; index++, cachedscr++, dscr++ ) {

    if ( SignalInterrupt ) return pushexception( E_SIGNAL );

    if ( dscr->sampling > 1 ) return pushexception( E_TOMODATA );

    cachedscr->number = dscr->number;
    cachedscr->len[0] = dscr->len[0] / sampling;
    cachedscr->len[1] = dscr->len[1] / sampling;
    cachedscr->low[0] = dscr->low[0];
    cachedscr->low[1] = dscr->low[1];
    cachedscr->type = dscr->img.type;
    cachedscr->attr = dscr->img.attr;
    memcpy( cachedscr->checksum, dscr->checksum, sizeof(cachedscr->checksum) );

    dstlen[0] = cachedscr->len[0];
    dstlen[1] = cachedscr->len[1];
    dstsize = dstlen[1] * dstlen[0] * TypeGetSize( dscr->img.type );

    status = I3ioAlloc( cache->handle, index, dstsize, 0 );
    if ( pushexception( status ) ) return status;

    dstaddr = I3ioBeginWrite( cache->handle, index, 0, dstsize );
    status = testcondition( dstaddr == NULL );
    if ( status ) return status;

    srcaddr = TomodataBeginRead( datacache, dscr, index );
    status = testcondition( srcaddr == NULL );
    if ( status ) goto error1;

    switch ( dscr->img.type ) {
      case TypeUint8:  status = pushexception( Sample2dUint8Uint8  ( dscr->len, srcaddr, smp, ori, dstlen, dstaddr, ori, &param ) ); break;
      case TypeUint16: status = pushexception( Sample2dUint16Uint16( dscr->len, srcaddr, smp, ori, dstlen, dstaddr, ori, &param ) ); break;
      case TypeUint32: status = pushexception( Sample2dUint32Uint32( dscr->len, srcaddr, smp, ori, dstlen, dstaddr, ori, &param ) ); break;
      case TypeInt8:   status = pushexception( Sample2dInt8Int8    ( dscr->len, srcaddr, smp, ori, dstlen, dstaddr, ori, &param ) ); break;
      case TypeInt16:  status = pushexception( Sample2dInt16Int16  ( dscr->len, srcaddr, smp, ori, dstlen, dstaddr, ori, &param ) ); break;
      case TypeInt32:  status = pushexception( Sample2dInt32Int32  ( dscr->len, srcaddr, smp, ori, dstlen, dstaddr, ori, &param ) ); break;
      case TypeReal:   status = pushexception( Sample2dRealReal    ( dscr->len, srcaddr, smp, ori, dstlen, dstaddr, ori, &param ) ); break;
      default:         status = pushexception( E_TOMODATA_TYP );
    }
    if ( status ) goto error2;

    status = TomodataEndRead( datacache, dscr, index, srcaddr );
    if ( exception( status ) ) goto error1;

    status = I3ioEndWrite( cache->handle, index, 0, dstsize, dstaddr );
    if ( exception( status ) ) return status;

    dscr->sampling = sampling;
    dscr->B1[0][0] = sampling;     dscr->B1[0][1] = 0;
    dscr->B1[1][0] = 0;            dscr->B1[1][1] = sampling;
    dscr->B1[2][0] = dscr->low[0]; dscr->B1[2][1] = dscr->low[1];

    status = Transf2Inv( dscr->B1, dscr->B1, NULL );
    if ( status ) return pushexception( status );

    dscr->handle = NULL;
    dscr->len[0] = dstlen[0];
    dscr->len[1] = dstlen[1];
    dscr->low[0] = 0;
    dscr->low[1] = 0;
    dscr->size = dscr->len[0] * dscr->len[1];
    dscr->offs = 0;

    if ( data->flags & TomoLog ) {
      char logbuf[logbuflen];
      TomodataLogString( data, datadscr, index, logbuf, logbuflen );
      MessageFormat( "%s sampling %"SizeU"\n", logbuf, sampling );
    }

  }

  return E_NONE;

  error2: TomodataEndRead( datacache, dscr, index, srcaddr );
  error1: I3ioEndWrite( cache->handle, index, 0, dstsize, dstaddr );

  return status;

}
