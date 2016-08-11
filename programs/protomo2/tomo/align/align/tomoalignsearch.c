/*----------------------------------------------------------------------------*
*
*  tomoalignsearch.c  -  align: series alignment
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
#include "imagemask.h"
#include "array.h"
#include "nmmin.h"
#include "mat2.h"
#include "transf2.h"
#include "message.h"
#include "exception.h"
#include "signals.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* types */

typedef struct {
  const Tomoseries *series;
  const Tomowindow *window;
  Coord Ap[3][2];
  Size index;
  Coord (*Apr)[2];
  Size prev;
  Real *imgaddr;
  Cmplx *fouaddr;
  Cmplx *tmpaddr;
  const Cmplx *refaddr;
  const char *log;
} TomoalignData;


/* functions */

static Status TomoalignCorr
              (TomoalignData *data,
               Coord Ap[3][2],
               Coord pos[2],
               Coord *pk)

{
  const Tomoseries *series = data->series;
  const Tomowindow *window = data->window;
  const Cmplx *refaddr = data->refaddr;
  Cmplx *fouaddr = data->fouaddr;
  Real *imgaddr = data->imgaddr;
  Size index = data->index;
  Size prev = data->prev;
  Status status;

  status = TomoseriesResample( series, &window->win, index, Ap, imgaddr, NULL, window->winmsk );
  if ( status ) goto error;

  status = WindowTransform( &window->fou, imgaddr, fouaddr, NULL, NULL );
  if ( status ) goto error;

  if ( ( window->corflt > 0 ) && ( prev != SizeMax ) ) {
    Coord A[3][2], B[3][2];
    TomoseriesResampleTransform( series, index, Ap, A );
    status = Transf2Inv( A, B, NULL );
    if ( status ) goto error;
    pos[0] = B[2][0];
    pos[1] = B[2][1];
    TomoseriesResampleTransform( series, prev, data->Apr, A );
    status = Transf2Inv( A, B, NULL );
    if ( status ) goto error;
    pos[0] -= B[2][0];
    pos[1] -= B[2][1];
  }

  Real peak;
  status = TomowindowCorr( window, refaddr, 0, fouaddr, NULL, data->tmpaddr, imgaddr, NULL, pos, &peak );
  if ( status ) goto error;
  *pk = peak;

  return E_NONE;

  error: ExceptionClear();

  return status;

}


static Status TomoalignMatch
              (Size n,
               const Coord *par,
               Size m,
               Coord *fn,
               void *fndata,
               Size *fcount)

{
  TomoalignData *data = fndata;
  Coord Ap[3][2];
  Coord pos[2];
  Status status;

  fn[0] = CoordMax; /* indicate function value not computed */

  if ( SignalInterrupt ) return E_SIGNAL;

  Ap[0][0] = data->Ap[0][0] + par[0];
  Ap[0][1] = data->Ap[0][1] + par[1];
  Ap[1][0] = data->Ap[1][0] + par[2];
  Ap[1][1] = data->Ap[1][1] + par[3];
  Ap[2][0] = data->Ap[2][0];
  Ap[2][1] = data->Ap[2][1];

  status = TomoalignCorr( data, Ap, pos, fn );
  if ( status ) return status;

  fn[0] = -fn[0]; /* negative, because searching minimum */
  fn[1] = pos[0];
  fn[2] = pos[1];

  (*fcount)++; /* call count */

  return E_NONE;

}


static Status TomoalignGridsearch
              (TomoalignData *data,
               Coord step,
               Coord limit,
               Coord Ap[3][2],
               Coord par[2],
               Coord sh[2],
               Coord *pk)

{
  Coord pos[2];
  Coord peak;
  Coord max[2];
  Status status;

  if ( SignalInterrupt ) return E_SIGNAL;

  par[0] = 1;
  par[1] = 0;
  par[3] = 0;

  status = TomoalignCorr( data, data->Ap, sh, pk );
  if ( exception( status ) ) return status;

  Ap[2][0] = data->Ap[2][0];
  Ap[2][1] = data->Ap[2][1];

  Coord rot = step;

  while ( rot <= limit ) {

    if ( SignalInterrupt ) return E_SIGNAL;

    par[0] = cos( rot * Pi / 180 );
    par[1] = sin( rot * Pi / 180 );

    Ap[0][0] =  par[0]; Ap[0][1] = par[1];
    Ap[1][0] = -par[1]; Ap[1][1] = par[0];
    Mat2Mul( data->Ap, Ap, Ap );

    status = TomoalignCorr( data, Ap, pos, &peak );
    if ( exception( status ) ) return status;

    if ( peak > *pk ) {
      *pk = peak;
      sh[0] = pos[0];
      sh[1] = pos[1];
      max[0] = par[0];
      max[1] = par[1];
      par[3] = rot;
    }

    par[1] = -par[1];

    Ap[0][0] =  par[0]; Ap[0][1] = par[1];
    Ap[1][0] = -par[1]; Ap[1][1] = par[0];
    Mat2Mul( data->Ap, Ap, Ap );

    status = TomoalignCorr( data, Ap, pos, &peak );
    if ( exception( status ) ) return status;

    if ( peak > *pk ) {
      *pk = peak;
      sh[0] = pos[0];
      sh[1] = pos[1];
      max[0] = par[0];
      max[1] = par[1];
      par[3] = -rot;
    }

    rot += step;

  }

  if ( par[3] != 0 ) {

    par[0] = max[0];
    par[1] = max[1];

    Ap[0][0] =  par[0]; Ap[0][1] = par[1];
    Ap[1][0] = -par[1]; Ap[1][1] = par[0];
    Mat2Mul( data->Ap, Ap, Ap );

  } else {

    Ap[0][0] = CoordMax;

  }

  par[0] -= 1;

  return E_NONE;

}


extern Status TomoalignSearch
              (Size thread,
               const void *inarg,
               void *outarg)

{
  const TomoalignInput *in = inarg;
  TomoalignOutput *out = outarg;
  Tomoalign *align = out->align;
  Status status = E_NONE;

  Cmplx *refaddr = TomorefTransform( align->ref, out->sortprev, out->indexprev, in->sort, in->index );
  status = testcondition( refaddr == NULL );
  if ( status ) return status;

  const Tomoseries *series = align->series;
  const Tomodata *data = series->data;
  Size index = in->sort[in->index];

  char logbuf[TomoalignLogbuflen];
  TomodataLogString( data, data->dscr, index, logbuf, TomoalignLogbuflen );

  const Tomowindow *window = align->window;
  const WindowFourier *fouwin = &window->fou;

  Real refpwr;
  status = WindowFourierPower( fouwin, refaddr, &refpwr );
  if ( pushexception( status ) ) goto exit1;
  if ( debug ) {
    MessageFormat( "%s  ref power %12.5"RealE"\n", logbuf, refpwr );
  }

  TomoimageList *list = align->image->list + index;
  list->flags &= ~( TomoimageDone | TomoimageFull );

  TomoalignData aligndata;
  aligndata.series = series;
  aligndata.window = window;
  aligndata.index = index;
  aligndata.refaddr = refaddr;
  aligndata.log = logbuf;

  if ( ( align->flags & TomoflagZeroRot ) || ( out->Ae[0][0] != CoordMax ) ) {
    aligndata.Ap[0][0] = list->Am[0][0]; aligndata.Ap[0][1] = list->Am[0][1];
    aligndata.Ap[1][0] = list->Am[1][0]; aligndata.Ap[1][1] = list->Am[1][1];
    if ( out->Ae[0][0] != CoordMax ) {
      Mat2Mul( aligndata.Ap, out->Ae, aligndata.Ap );
    }
  } else {
    aligndata.Ap[0][0] = list->Ap[0][0]; aligndata.Ap[0][1] = list->Ap[0][1];
    aligndata.Ap[1][0] = list->Ap[1][0]; aligndata.Ap[1][1] = list->Ap[1][1];
  }
  aligndata.Ap[2][0] = list->Ap[2][0]; aligndata.Ap[2][1] = list->Ap[2][1];

  if ( out->sortprev == NULL ) {
    aligndata.prev = SizeMax;
    aligndata.Apr = NULL;
  } else {
    aligndata.prev = out->sortprev[out->indexprev];
    aligndata.Apr = align->image->list[aligndata.prev].Ap;
  }

  aligndata.tmpaddr = malloc( 3 * fouwin->fousize * sizeof(Cmplx) );
  if ( aligndata.tmpaddr == NULL ) { status = pushexception( E_MALLOC ); goto exit1; }
  aligndata.fouaddr = aligndata.tmpaddr + fouwin->fousize;
  aligndata.imgaddr = (Real *)( aligndata.fouaddr + fouwin->fousize );

  out->term = NULL;

  Coord *sh = out->sh;
  Coord pk = -CoordMax;
  Coord par[4] = { 0, 0, 0, 0 };

  if ( align->flags & TomoflagMatch ) {

    Coord step[4] = { 0.01, 0.01, 0.01, 0.01 };
    NMdata nmdata = NMdataInitializer;
    nmdata.step = step;
    nmdata.log = aligndebug ? logbuf : NULL;

    Coord fmin[3];
    status = NMmin( 4, par, TomoalignMatch, &aligndata, &nmdata, par, 3, fmin );
    if ( status ) {
      if ( ( status != E_NMMIN_FAIL ) || ( fmin[0] != CoordMax ) ) {
        pushexception( status ); goto exit2;
      } else {
        pk = -CoordMax;
        goto exit3;
      }
    }

    pk = -fmin[0];
    sh[0] = fmin[1];
    sh[1] = fmin[2];

    if ( align->transmax > 0 ) {
      if ( sh[0] * sh[0] + sh[1] * sh[1] > align->transmax * align->transmax ) {
        pk = -CoordMax;
        goto exit3;
      }
    }

    aligndata.Ap[0][0] += par[0];
    aligndata.Ap[0][1] += par[1];
    aligndata.Ap[1][0] += par[2];
    aligndata.Ap[1][1] += par[3];

  } else {

    Coord Ap[3][2];

    status = TomoalignGridsearch( &aligndata, align->grid.step, align->grid.limit, Ap, par, sh, &pk );
    if ( pushexception( status ) ) goto exit2; 

    if ( align->transmax > 0 ) {
      if ( sh[0] * sh[0] + sh[1] * sh[1] > align->transmax * align->transmax ) {
        pk = -CoordMax;
        goto exit3;
      }
    }

    if ( Ap[0][0] != CoordMax ) {
      aligndata.Ap[0][0] = Ap[0][0];
      aligndata.Ap[0][1] = Ap[0][1];
      aligndata.Ap[1][0] = Ap[1][0];
      aligndata.Ap[1][1] = Ap[1][1];
    }

  }

  Real foupwr;
  status = WindowFourierPower( fouwin, aligndata.fouaddr, &foupwr );
  if ( pushexception( status ) ) goto exit2;
  if ( debug ) {
    MessageFormat( "%s  img power %12.5"RealE"\n", logbuf, foupwr );
  }

  Real norm = FnSqrt( refpwr * foupwr );
  pk /= norm;

  if ( align->cor != NULL ) {
    status = TomoalignCorrWrite( align->cor, index, window->img.len, aligndata.imgaddr, window->corlen, (Real *)aligndata.tmpaddr, norm );
    if ( exception( status ) ) goto exit2;
  }

  Coord c[2];
  Mat2TranspMulVec( aligndata.Ap, sh, c );
  c[0] *= series->sampling;
  c[1] *= series->sampling;

  aligndata.Ap[2][0] += c[0];
  aligndata.Ap[2][1] += c[1];

  if ( align->maxshift > 0 ) {
    if ( c[0] * c[0] + c[1] * c[1] > align->maxshift * align->maxshift ) {
      out->term = "max shift exceeded";
    }
  }

  if ( align->flags & TomoflagMatch ) {
    if ( align->maxcorr > 0 ) {
      Coord corr[2];
      status = TomogeomCorr( list->Am, aligndata.Ap, NULL, corr, NULL );
      if ( exception( status ) ) goto exit2;
      if ( align->maxcorr > 0 ) {
        if ( ( Fabs( corr[0] - 1 ) > align->maxcorr ) || ( Fabs( corr[1] - 1 ) > align->maxcorr ) ) {
          out->term = "max correction exceeded";
        }
      }
    }
  }

  if ( out->term == NULL ) {
    status = TomoimageSet( list, aligndata.Ap, TomoimageDone | TomoimageFull );
    if ( pushexception( status ) ) goto exit2;
    memcpy( series->geom[index].Aa, aligndata.Ap, sizeof(aligndata.Ap) );
  }

  exit3: out->pk = pk;

  if ( align->flags & TomoLog ) {

    char ccc[64] = "  skipped";
    if ( pk != -CoordMax ) {
      if ( pk >  9.99999 ) pk =  9.99999;
      if ( pk < -9.99999 ) pk = -9.99999;
      sprintf( ccc, "  ccc %7.5f%s", pk, ( out->term == NULL ) ? "" : " *" );
    }

    MessageFormat( "%s  max @ %7.3f %7.3f  %9.4f %9.4f %9.4f %9.4f; %s\n", logbuf, sh[0], sh[1], par[0], par[1], par[2], par[3], ccc );

  }

  exit2: free( aligndata.tmpaddr );

  exit1: free( refaddr );

  return status;

}


extern Status TomoalignSearchDryrun
              (Size thread,
               const void *inarg,
               void *outarg)

{
  const TomoalignInput *in = inarg;
  TomoalignOutput *out = outarg;
  Tomoalign *align = out->align;

  if ( align->flags & TomoLog ) {
    TomoalignDryrunLog( align, in->sort[in->index] );
  }

  return E_NONE;

}
