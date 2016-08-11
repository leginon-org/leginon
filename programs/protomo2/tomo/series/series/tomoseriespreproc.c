/*----------------------------------------------------------------------------*
*
*  tomoseriespreproc.c  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseries.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status TomoseriesPreproc
              (const Tomoseries *series,
               const Size index,
               Image *img,
               void **addr)

{
  Image dst;
  uint8_t *mskaddr = NULL;
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( img  == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  if ( index >= series->tilt->images ) return pushexception( E_ARGVAL );

  Tomodata *data = series->data;
  TomodataDscr *dscr = data->dscr + index;

  void *srcaddr = TomodataBeginRead( data->cache, dscr, index );
  status = testcondition( srcaddr == NULL );
  if ( status ) return status;

  status = ImageMetaCopyAlloc( &dscr->img, &dst, 0 );
  if ( pushexception( status ) ) goto error1;

  void *dstaddr = malloc( dst.len[0] * dst.len[1] * TypeGetSize( dst.type ) );
  if ( dstaddr == NULL ) { status = pushexception( E_MALLOC ); goto error2; }

  status = TomodataPreprocImage( data, dscr, srcaddr, dstaddr, &mskaddr );
  if ( pushexception( status ) ) goto error3;

  status = TomodataEndRead( data->cache, dscr, index, srcaddr );
  if ( exception( status ) ) goto error3;

  if ( mskaddr != NULL ) free( mskaddr );

  *img = dst;
  *addr = dstaddr;

  return E_NONE;

  error3: free( dstaddr ); if ( mskaddr != NULL ) free( mskaddr );
  error2: free( dst.len ); free( dst.low );
  error1: TomodataEndRead( data->cache, dscr, index, srcaddr );

  return status;

}
