/*----------------------------------------------------------------------------*
*
*  seq.h  -  core: sequence generator
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef seq_h_
#define seq_h_

#include "defs.h"

#define SeqName   "seq"
#define SeqVers   COREVERS"."COREBUILD
#define SeqCopy   CORECOPY


/* exception codes */

enum {
  E_SEQ = SeqModuleCode,
  E_SEQ_MAXCODE
};


/* types */

struct _Seq;

typedef struct _Seq Seq;

typedef struct {
  Coord step;
  Coord limit;
  Bool mat;
} SeqRotParam;

typedef struct {
  Coord polstep;
  Coord pollimit;
  Coord spnstep;
  Coord spnlimit;
  Bool mat;
} SeqEulParam;

typedef union {
  SeqRotParam rot;
  SeqEulParam eul;
} SeqParam;


/* prototypes */

extern Seq *SeqRotInit
            (const SeqParam *param);

extern Status SeqRotNext
              (Seq *seq,
               void *arg);

extern Seq *SeqEulInit
            (const SeqParam *param);

extern Status SeqEulNext
              (Seq *seq,
               void *arg);

#endif
