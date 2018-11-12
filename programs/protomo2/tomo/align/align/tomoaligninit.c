/*----------------------------------------------------------------------------*
*
*  tomoaligninit.c  -  align: series alignment
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
#include "message.h"
#include "macros.h"
#include "exception.h"


/* functions */

static Size TomoalignCount
            (const TomotiltGeom *geom,
             const Tomoimage *image,
             Coord maxangle)

{
  const TomoimageList *list = image->list;
  Size count = image->count;

  if ( maxangle <= 0 ) maxangle = 90;

  for ( Size index = 0; index < count; index++ ) {

    Size min = image->min[index];
    if ( ( min < SizeMax ) && ( list[min].flags & TomoimageAli ) ) {
      if ( Fabs( geom[min].theta ) > maxangle ) return index;
    }

    Size max = image->max[index];
    if ( ( max < SizeMax ) && ( list[max].flags & TomoimageAli ) ) {
      if ( Fabs( geom[max].theta ) > maxangle ) return index;
    }

  }

  return count;

}


static Size TomoalignMaxStart
            (const TomotiltImage *tiltimage,
             const Tomoimage *image,
             Size count,
             Size number)

{
  const TomoimageList *list = image->list;

  for ( Size index = 0; index < count; index++ ) {

    Size min = image->min[index];
    if ( ( min < SizeMax ) && ( list[min].flags & TomoimageSel ) ) {
      if ( tiltimage[min].number == number ) return index;
    }

    Size max = image->max[index];
    if ( ( max < SizeMax ) && ( list[max].flags & TomoimageSel ) ) {
      if ( tiltimage[max].number == number ) return index;
    }

  }

  return count;

}


extern Status TomoalignInit
              (Tomoalign *align,
               const TomoalignParam *aliparam,
               const TomowindowParam *winparam,
               const TomorefParam *refparam)

{
  Status status;

  if ( argcheck( align == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( aliparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( winparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( refparam == NULL ) ) return pushexception( E_ARGVAL );

  const Tomoseries *series = align->series;
  if ( series == NULL ) return pushexception( E_TOMOALIGN );

  if ( align->window != NULL ) return pushexception( E_TOMOALIGN );
  if ( align->image != NULL ) return pushexception( E_TOMOALIGN );
  if ( align->ref != NULL ) return pushexception( E_TOMOALIGN );

  Tomoimage *image = TomoimageCreate( series, aliparam->selection, aliparam->exclusion, aliparam->startangle );
  status = testcondition( image == NULL );
  if ( status ) return status;
  align->image = image;

  Tomoref *ref = TomorefCreate( series );
  status = testcondition( ref == NULL );
  if ( status ) return status;
  align->ref = ref;

  Tomowindow *window = TomowindowCreate( winparam );
  status = testcondition( window == NULL );
  if ( status ) return status;
  align->window = window;

  status = TomowindowCorrInit( window, &aliparam->corr );
  if ( pushexception( status ) ) return status;

  align->count = TomoalignCount( series->tilt->tiltgeom, image, aliparam->maxangle );
  if ( !align->count ) return pushexception( E_TOMOALIGN_RNG );

  align->start = 0;
  align->maxshift = aliparam->maxshift;
  align->maxcorr = aliparam->maxcorr;
  align->transmax = aliparam->transmax;
  align->grid = aliparam->grid;
  align->flags = aliparam->flags & ( TomoflagMask | TomoflagMaskWrt | TomoflagAlignMask );

  if ( align->flags & TomoDryrun ) {
    align->flags &= ~TomoflagMaskWrt;
    ref->flags |= TomoDryrun;
    window->corlen[0] = window->corlen[1] = 0;
  }

  if ( align->grid.step <= 0 ) {
    align->flags |= TomoflagMatch;
    ref->flags |= TomoflagMatch;
  }

  if ( ~align->flags & TomoRestart ) {
    align->start = TomoalignMaxStart( series->tilt->tiltimage, image, align->count, aliparam->startimage );
  }

  status = TomorefInit( ref, image, &window->img, &window->fou, refparam );
  if ( exception( status ) ) return status;

  if ( window->corlen[0] && window->corlen[1] ) {
    window->corlen[0] = MIN( window->corlen[0], window->img.len[0] );
    window->corlen[1] = MIN( window->corlen[1], window->img.len[1] );
    Index low[2] = { -(Index)( window->corlen[0] / 2 ), -(Index)( window->corlen[1] / 2 ) };
    Image image = { 2, window->corlen, low, TypeReal, ImageAsym };
    char *sffx = ( align->flags & TomoflagCorr ) ? "_ccf.img" : "_cor.img";
    align->cor = TomodiagnCreate( series, sffx, &image );
    status = testcondition( align->cor == NULL );
    if ( status ) return status;
  }

  return E_NONE;

}


extern Status TomoalignFinal
              (Tomoalign *align)

{
  Status stat, status = E_NONE;

  if ( argcheck( align == NULL ) ) return pushexception( E_ARGVAL );

  if ( align->cor != NULL ) {
    stat = TomodiagnClose( align->cor );
    if ( exception( stat ) ) status = stat;
    align->cor = NULL;
  }

  if ( align->window != NULL ) {
    stat = TomowindowDestroy( align->window );
    if ( exception( stat ) ) status = stat;
    align->window = NULL;
  }

  if ( align->ref != NULL ) {
    stat = TomorefDestroy( align->ref );
    if ( exception( stat ) ) status = stat;
    align->ref = NULL;
  }

  if ( align->image != NULL ) {
    stat = TomoimageDestroy( align->image );
    if ( exception( stat ) ) status = stat;
    align->image = NULL;
  }

  return status;

}
