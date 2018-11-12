/*----------------------------------------------------------------------------*
*
*  tomoalignexec.c  -  align: series alignment
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
#include "mat2.h"
#include "message.h"
#include "thread.h"
#include "exception.h"
#include "macros.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status TomoalignEstimate
              (Coord Am[3][3],
               Coord Ap[2][2],
               Coord Ae[2][2])

{
  Status status;

  Ae[0][0] = Am[0][0]; Ae[0][1] = Am[0][1];
  Ae[1][0] = Am[1][0]; Ae[1][1] = Am[1][1];

  status = Mat2Inv( Ae, Ae, NULL );
  if ( pushexception( status ) ) return status;

  Mat2Mul( Ae, Ap, Ae );

  return E_NONE;

}


static void TomoalignEval
            (const TomoalignOutput *out,
             Size *count,
             Coord *sh,
             Coord *ccc)

{

  (*count)++;

  sh[0] += out->sh[0] * out->sh[0];
  sh[1] += out->sh[1] * out->sh[1];

  *ccc  += out->pk * out->pk;

}


static Status TomoalignExecThread
              (Thread *thread,
               Size *count,
               const Tomoseries *series,
               TomoimageList *list,
               const Size *sort,
               Size sortindex,
               Tomoflags flags,
               TomoalignInput *in,
               TomoalignOutput *out)

{

  Size index = sort[sortindex];
  Status status;

  if ( ( index < SizeMax ) && ( list[index].flags & TomoimageAli ) ) {

    status = TomoimageGet( series, list, index, !!( flags & TomoflagMatch ) );
    if ( pushexception( status ) ) return status;

    in->sort = sort;
    in->index = sortindex;

    thread[*count].function = ( flags & TomoDryrun ) ? TomoalignSearchDryrun : TomoalignSearch;
    thread[*count].inarg = in;
    thread[*count].outarg = out;
    (*count)++;

  }

  return E_NONE;

}


static Status TomoalignExecSet
              (const Tomoseries *series,
               TomoimageList *list,
               Tomoflags flags,
               TomoalignInput *in,
               TomoalignOutput *out,
               Size *count,
               Coord *sh,
               Coord *ccc)

{
  Status status;

  if ( out->term == NULL ) {

    Size index = in->sort[in->index];
    list += index;

    if ( ~flags & TomoDryrun ) {

      TomoalignEval( out, count, sh, ccc );

      status = TomometaSetTransf( series->meta, index, list->Ap, !!( flags & TomoflagMatch ) );
      if ( exception( status ) ) return status;

      if ( flags & TomoflagEstimate ) {
        status = TomoalignEstimate( list->Am, list->Ap, out->Ae );
        if ( exception( status ) ) return status;
      }

    }

    if ( list->flags & TomoimageRef ) {
      out->sortprev = in->sort;
      out->indexprev = in->index;
    }

  } else {

    if ( flags & TomoLog ) Message( out->term, "\n" );

  }

  return E_NONE;

}


extern Status TomoalignExec
              (Tomoalign *align)

{
  Status status;

  if ( argcheck( align == NULL ) ) return pushexception( E_ARGVAL );

  if ( align->flags & TomoLog ) {
    if ( align->flags & TomoDryrun ) {
      Message( "dry run...", "\n" );
    }
    Message( "initializing reference...", "\n" );
  }

  Tomoref *ref = align->ref;
  if ( ref == NULL ) return pushexception( E_TOMOALIGN );

  status = TomorefStart( ref, align->start );
  if ( exception( status ) ) return status;

  status = TomorefNew( ref, SizeMax );
  if ( exception( status ) ) return status;

  Tomoflags flags = align->flags;
  if ( flags & TomoLog ) {
    Message( ( align->flags & TomoflagMatch ) ? "area matching" : "grid search", "...\n" );
  }

  const Tomoseries *series = align->series;
  const Tomoimage *image = align->image;
  TomoimageList *list = image->list;

  TomoalignOutput outmin = TomoalignOutputInitializer;
  TomoalignOutput outmax = TomoalignOutputInitializer;

  outmin.align = align;
  outmax.align = align;

  Size aligned = 0;
  Coord sh[2] = { 0, 0 };
  Coord ccc = 0;

  Size mincount = ref->mincount;
  Size maxcount = ref->maxcount;

  for ( Size index = MIN( mincount, maxcount ); index < image->count; index++ ) {

    status = TomorefUpdate( ref, mincount, maxcount );
    if ( exception( status ) ) return status;

    Thread thread[2];
    Size count = 0;

    TomoalignInput inmin = TomoalignInputInitializer;
    TomoalignInput inmax = TomoalignInputInitializer;

    if ( index == mincount ) {
      status = TomoalignExecThread( thread, &count, series, list, image->min, index, flags, &inmin, &outmin );
      if ( exception( status ) ) return status;
      mincount++;
    }

    if ( index == maxcount ) {
      status = TomoalignExecThread( thread, &count, series, list, image->max, index, flags, &inmax, &outmax );
      if ( exception( status ) ) return status;
      maxcount++;
    }

    if ( count ) {

      status = ThreadExec( count, thread );
      if ( status ) {
        if ( status == E_THREAD_ERROR ) {
          logexception( status );
        } else {
          pushexception( status );
        }
        return status;
      }

      if ( inmin.sort != NULL ) {
        status = TomoalignExecSet( series, list, flags, &inmin, &outmin, &aligned, sh, &ccc );
        if ( exception( status ) ) return status;
      }

      if ( inmax.sort != NULL ) {
        status = TomoalignExecSet( series, list, flags, &inmax, &outmax, &aligned, sh, &ccc );
        if ( exception( status ) ) return status;
      }

      if ( ( outmin.term != NULL ) || ( outmax.term != NULL ) ) break;

    }

  }

  if ( flags & TomoLog ) {

    if ( aligned ) {
      MessageFormat( "rms shift %7.3f %7.3f;  rms ccc %7.5f\n", Sqrt( sh[0] / aligned ), Sqrt( sh[1] / aligned ), Sqrt( ccc / aligned ) );
    }

    Message( ( align->flags & TomoflagMatch ) ? "end matching" : "end grid search", ".\n" );

  }

  return E_NONE;

}
