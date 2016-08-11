/*----------------------------------------------------------------------------*
*
*  seqrot.c  -  core: sequence generator
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "seq.h"
#include "mat2.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* types */

struct _Seq {
  Size count;
  Coord phi;
  SeqRotParam rot;
};


/* functions */

extern Seq *SeqRotInit
            (const SeqParam *param)

{

  if ( param == NULL ) { pushexception( E_ARGVAL ); return NULL; }

  Seq *seq = malloc( sizeof(*seq) );
  if ( seq == NULL ) { pushexception( E_MALLOC ); return NULL; }

  seq->count = 0;
  seq->rot = param->rot;

  if ( seq->rot.step <  0 ) seq->rot.step = -seq->rot.step;
  if ( seq->rot.step == 0 ) seq->rot.step = 360;

  if ( seq->rot.limit > 180 ) seq->rot.limit = 180;

  return seq;

}


static Status Mat2Unit180
              (Coord A[2][2])

{

  A[0][0] = -1;  A[0][1] =  0;
  A[1][0] =  0;  A[1][1] = -1;

  return E_NONE;

}


extern Status SeqRotNext
              (Seq *seq,
               void *arg)

{
  Coord *a = arg;

  if ( seq == NULL ) return exception( E_ARGVAL );
  if ( arg == NULL ) return exception( E_ARGVAL );

  if ( !seq->count ) {

    if ( seq->rot.mat ) {
      Mat2Unit( arg );
    } else {
      *a = 0;
    }
    seq->count = 1;
    seq->phi = seq->rot.step;

  } else {

    if ( seq->phi > seq->rot.limit ) {
      free( seq );
      return E_EOF;
    }

    if ( seq->phi == 180 ) {

      if ( seq->rot.mat ) {
        Mat2Unit180( arg );
      } else {
        *a = 180;
      }
      seq->count++;
      seq->phi = 360;

    } else {

      if ( seq->rot.mat ) {
        Coord phi = seq->phi * Pi / 180;
        Mat2Rot( &phi, arg );
      } else {
        *a = seq->phi;
      }
      if ( seq->phi > 0 ) {
        seq->phi = -seq->phi;
      } else {
        seq->phi = ++seq->count * seq->rot.step;
      }

    }

  }

  return E_NONE;

}
