/*----------------------------------------------------------------------------*
*
*  tomoalignseriescorr.c  -  align: series alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoaligncommon.h"
#include "imagearray.h"
#include "message.h"
#include "macros.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

static Status TomoalignSeriesCorrImage
              (const Tomoalign *align,
               const Size *sort,
               Size sortindex,
               Real *r,
               Real *imgbuf,
               Cmplx *imgfou)

{
  Status status;

  const Tomoseries *series = align->series;
  const Tomoimage *image = align->image;
  TomoimageList *list = image->list;
  Tomoref *ref = align->ref;

  Size index = ( sortindex == SizeMax ) ? image->cooref : sort[sortindex];
  if ( index == SizeMax ) return E_NONE;

  status = TomoimageGet( series, list, index, True );
  if ( pushexception( status ) ) return status;

  status = TomorefNew( ref, index );
  if ( exception( status ) ) return status;

  if ( ref->flags & TomoDryrun ) {
    TomoalignDryrunLog( align, index );
    return E_NONE;
  }

  char logbuf[TomoalignLogbuflen];
  TomodataLogString( series->data, series->data->dscr, index, logbuf, TomoalignLogbuflen );

  Cmplx *reffou = TomorefTransform( ref, NULL, SizeMax, sort, sortindex );
  status = testcondition( reffou == NULL );
  if ( status ) return status;

  const Tomowindow *window = align->window;
  const Window *imgwin = &window->win;
  const WindowFourier *fouwin = &window->fou;

  Real refpwr;
  status = WindowFourierPower( fouwin, reffou, &refpwr );
  if ( pushexception( status ) ) goto exit;
  if ( debug ) {
    MessageFormat( "%s  ref power %12.5"RealE"\n", logbuf, refpwr );
  }

  status = TomoseriesResample( series, imgwin, index, list[index].Ap, imgbuf, NULL, NULL );
  if ( status ) goto exit;

  Real imgpwr;
  status = WindowTransform( fouwin, imgbuf, imgfou, &imgpwr, NULL );
  if ( status ) goto exit;
  if ( debug ) {
    MessageFormat( "%s  img power %12.5"RealE"\n", logbuf, imgpwr );
  }

  Real norm;
  Coord pos[2]; Real peak;
  status = TomowindowCorr( window, reffou, refpwr, imgfou, &imgpwr, imgfou, imgbuf, &norm, pos, &peak );
  if ( pushexception( status ) ) goto exit;

  Coord pk0 = ( norm > 0 ) ? imgbuf[0] / norm : 0;
  Coord pkmax = peak;
  if ( r != NULL ) r[index] = pk0;
  if ( debug ) {
    MessageFormat( "%s  corr[0] %12.5"CoordE"   corr max %12.5"CoordE"\n", logbuf, pk0, pkmax );
  }

  if ( align->cor != NULL ) {
    status = TomoalignCorrWrite( align->cor, index, imgwin->len, imgbuf, window->corlen, (Real *)imgfou, norm );
    if ( exception( status ) ) goto exit;
  }

  if ( align->flags & TomoLog ) {
    if ( pk0 >  9.99999 ) pk0 =  9.99999;
    if ( pk0 < -9.99999 ) pk0 = -9.99999;
    if ( pkmax >  9.99999 ) pkmax =  9.99999;
    if ( pkmax < -9.99999 ) pkmax = -9.99999;
    MessageFormat( "%s  max @ %7.3f %7.3f  %7.5f   ccc %7.5f\n", logbuf, pos[0], pos[1], pkmax, pk0 );
  }

  exit: free( reffou );

  return status;

}


static Status TomoalignSeriesCorrSub
              (Tomoalign *align,
               Real *r,
               const TomoalignParam *param)

{
  Status status;

  Tomoflags flags = align->flags;
  if ( flags & TomoLog ) {
    Message( "correlating...", "\n" );
  }

  if ( r != NULL ) {
    for ( Size index = 0; index < align->series->tilt->images; index++ ) {
      r[index] = -RealMax;
    }
  }

  const Tomowindow *window = align->window;
  const Window *imgwin = &window->win;
  const WindowFourier *fouwin = &window->fou;

  Real *imgbuf = WindowAlloc( imgwin );
  status = testcondition( imgbuf == NULL );
  if ( status ) return status;

  Cmplx *imgfou = WindowFourierAlloc( fouwin );
  status = testcondition( imgfou == NULL );
  if ( status ) goto exit1;

  const Tomoimage *image = align->image;

  status = TomoalignSeriesCorrImage( align, image->min, SizeMax, r, imgbuf, imgfou );
  if ( exception( status ) ) goto exit2;

  for ( Size index = 0; index < image->count; index++ ) {

    status = TomoalignSeriesCorrImage( align, image->min, index, r, imgbuf, imgfou );
    if ( exception( status ) ) goto exit2;

    status = TomoalignSeriesCorrImage( align, image->max, index, r, imgbuf, imgfou );
    if ( exception( status ) ) goto exit2;

  }

  exit2: free( imgfou );
  exit1: free( imgbuf );

  return status;

}


extern Status TomoalignSeriesCorr
              (Tomoseries *series,
               Real *r,
               const TomoalignParam *aliparam,
               const TomowindowParam *winparam,
               const TomorefParam *refparam)

{
  Status stat, status;

  if ( argcheck( series == NULL ) )   return pushexception( E_ARGVAL );
  if ( argcheck( aliparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( winparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( refparam == NULL ) ) return pushexception( E_ARGVAL );

  if ( ( refparam->mode.type != TomorefBck ) && ( refparam->mode.type != TomorefBpr ) ) {
    return pushexception( E_TOMOREF_TYPE );
  }

  Tomoflags seriesflags = series->flags;

  TomoalignParam alipar = *aliparam;
  series->flags |= alipar.flags & TomoflagAlignMask;
  if ( seriesflags & TomoLog ) {
    series->flags &= ~TomoLog;
    alipar.flags |= TomoLog;
  }

  alipar.flags |= TomoflagCorr;

  Tomoalign *align = TomoalignCreate( series );
  status = testcondition( align == NULL );
  if ( status ) goto error0;

  status = TomoalignInit( align, &alipar, winparam, refparam );
  if ( exception( status ) ) goto error1;

  status = TomoalignSeriesCorrSub( align, r, &alipar );
  if ( exception( status ) ) goto error1;

  stat = TomoalignDestroy( align );
  logexception( stat );

  series->flags = seriesflags;

  return status;

  error1: TomoalignDestroy( align );
  error0: series->flags = seriesflags;

  return status;

}
