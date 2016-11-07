/*----------------------------------------------------------------------------*
*
*  tomoseriesresample.c  -  series: tomography
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
#include "transform.h"
#include "linear.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>
#include <string.h>


/* functions */

#define logbuflen 96

extern Status TomoseriesResample
              (const Tomoseries *series,
               const Window *win,
               const Size index,
               Coord Ap[3][2],
               Real *winaddr,
               Stat *winstat,
               const MaskParam *winmsk)

{
  Coord Bp[3][2];
  Stat statbuf;
  char logbuf[logbuflen];
  Status status, stat;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( win == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( Ap == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( winaddr == NULL ) ) return pushexception( E_ARGVAL );

  Tomodata *data = series->data;
  TomodataDscr *dscr = data->dscr + index;
  if ( winstat == NULL ) winstat = &statbuf;

  TomoseriesResampleGeom( dscr, series->sampling, Ap, Bp );

  void *addr = TomodataBeginRead( data->cache, dscr, index );
  status = testcondition( addr == NULL );
  if ( status ) return status;

  status = WindowResample( dscr->img.len, dscr->img.type, addr, Bp[0], Bp[2], win, winaddr, winstat, winmsk );
  if ( status ) {
    if ( status == E_WINDOW_AREA ) {
      Coord a = winstat->count; a /= win->size;
      if ( series->flags & TomoLog ) {
        TomodataLogString( data, data->dscr, index, logbuf, logbuflen );
        MessageFormat( "%s resampled area is too small [%.1"CoordF"%%]\n", logbuf, 100 * a );
      }
      TomodataErrString( data->dscr, index, logbuf, logbuflen );
      pushexceptionmsg( status, ", ", logbuf );
    } else {
      pushexception( status );
    }
  } else if ( series->flags & TomoLog ) {
    TomodataLogString( data, data->dscr, index, logbuf, logbuflen );
    MessageFormat( "%s resampled\n", logbuf );
  }

  stat = TomodataEndRead( data->cache, dscr, index, addr );
  if ( exception( stat ) ) status = stat;

  return status;

}


extern Status TomoseriesResampleArea
              (const Tomoseries *series,
               const Window *win,
               const Size index,
               Coord Ap[3][2],
               uint16_t *winaddr)

{
  Coord Bp[3][2];
  uint16_t *buf;
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( win == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( winaddr == NULL ) ) return pushexception( E_ARGVAL );

  TomodataDscr *dscr = series->data->dscr + index;

  TomoseriesResampleGeom( dscr, series->sampling, Ap, Bp );

  Size imgsize;
  status = ArraySize( 2, dscr->img.len, sizeof(*buf), &imgsize );
  if ( pushexception( status ) ) return status;

  buf = malloc( imgsize * sizeof(*buf) );
  if ( buf == NULL ) return pushexception( E_MALLOC );
  memset( buf, 0, imgsize * sizeof(*buf) );

  TransformParam transform = TransformParamInitializer;
  transform.fill = 8;
  transform.flags = TransformFill;
  Linear2dUint16Uint16( dscr->img.len, buf, Bp[0], Bp[2], win->len, winaddr, NULL, &transform );

  for ( Size i = 0; i < win->size; i++ ) {
    winaddr[i] = winaddr[i] < 8;
  }

  free( buf );

  return E_NONE;

}
