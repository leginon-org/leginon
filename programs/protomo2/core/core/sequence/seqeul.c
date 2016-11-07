/*----------------------------------------------------------------------------*
*
*  seqeul.c  -  core: sequence generator
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
#include "mat3.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* types */

struct _Seq {
  Size polcount;
  Size psicount;
  Size spncount;
  Coord euler[3];
  Size npsi;
  Coord psistep;
  SeqEulParam eul;
};


/* functions */

extern Seq *SeqEulInit
            (const SeqParam *param)

{

  if ( param == NULL ) { pushexception( E_ARGVAL ); return NULL; }

  Seq *seq = malloc( sizeof(*seq) );
  if ( seq == NULL ) { pushexception( E_MALLOC ); return NULL; }

  seq->polcount = 0;
  seq->psicount = 0;
  seq->spncount = 0;
  seq->euler[0] = 0;
  seq->euler[1] = 0;
  seq->npsi = SizeMax;
  seq->eul = param->eul;

  if ( seq->eul.polstep <  0 ) seq->eul.polstep = -seq->eul.polstep;
  if ( seq->eul.polstep == 0 ) seq->eul.polstep = 360;

  if ( seq->eul.pollimit > 180 ) seq->eul.pollimit = 180;

  if ( seq->eul.spnstep <  0 ) seq->eul.spnstep = -seq->eul.spnstep;
  if ( seq->eul.spnstep == 0 ) seq->eul.spnstep = 360;

  if ( seq->eul.spnlimit > 180 ) seq->eul.spnlimit = 180;

  return seq;

}


static void SeqMat
            (Coord euler[3],
             Coord A[3][3])

{

  euler[0] *= Pi / 180;
  euler[1] *= Pi / 180;
  euler[2] *= Pi / 180;

  Mat3Rot( euler, A );

}


static Status SeqEulSpin
              (Seq *seq,
               void *arg)

{
  Coord *euler = seq->euler;
  Coord *eul = arg;

  if ( !seq->spncount ) {

    eul[0] = euler[0];
    eul[1] = euler[1];
    eul[2] = -euler[0];
    if ( seq->eul.mat ) SeqMat( eul, arg );

    euler[2] = seq->eul.spnstep;
    seq->spncount = 1;

  } else {

    if ( euler[2] > seq->eul.spnlimit ) return E_EOF;

    if ( euler[2] == 180 ) {

      eul[0] = euler[0];
      eul[1] = euler[1];
      eul[2] = 180 - euler[0];
      if ( seq->eul.mat ) SeqMat( eul, arg );

      euler[2] = 360;
      seq->spncount++;

    } else {

      eul[0] = euler[0];
      eul[1] = euler[1];
      eul[2] = euler[2] - euler[0];
      if ( seq->eul.mat ) SeqMat( eul, arg );

      if ( euler[2] > 0 ) {
        euler[2] = - euler[2];
      } else {
        euler[2] = ++seq->spncount * seq->eul.spnstep;
      }

    }

  }

  return E_NONE;

}


extern Status SeqEulNext
              (Seq *seq,
               void *arg)

{

  if ( seq == NULL ) return exception( E_ARGVAL );
  if ( arg == NULL ) return exception( E_ARGVAL );

  if ( !seq->polcount ) {

    if ( !SeqEulSpin( seq, arg ) ) return E_NONE;
    seq->spncount = 0;

    seq->euler[1] = seq->eul.polstep;
    seq->polcount = 1;

  }

  while ( seq->euler[1] <= seq->eul.pollimit ) {

    if ( !seq->psicount ) {

      if ( !seq->spncount ) {
        seq->npsi = Ceil ( 180 * Sin( seq->euler[1] * Pi / 180 ) / seq->eul.polstep );
        if ( seq->npsi < 2 ) seq->npsi = 2;
        seq->psistep = 180; seq->psistep /= seq->npsi;
      }

      if ( !SeqEulSpin( seq, arg ) ) return E_NONE;
      seq->spncount = 0;

      seq->euler[0] = seq->psistep;
      seq->psicount = 1;

    }

    if ( seq->psicount < seq->npsi ) {

      if ( !SeqEulSpin( seq, arg ) ) return E_NONE;
      seq->spncount = 0;

      if ( seq->euler[0] > 0 ) {
        seq->euler[0] = -seq->euler[0];
      } else {
        seq->euler[0] = ++seq->psicount * seq->psistep;
      }

    }

    if ( seq->psicount == seq->npsi ) {

      seq->euler[0] = 180;
      if ( !SeqEulSpin( seq, arg ) ) return E_NONE;
      seq->spncount = 0;

      seq->euler[1] = ++seq->polcount * seq->eul.polstep;
      seq->euler[0] = 0;
      seq->psicount = 0;

    }

  }

  free( seq );

  return E_EOF;

}
