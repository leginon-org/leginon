/*----------------------------------------------------------------------------*
*
*  tomotiltsemant.h  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomotiltsemant_h_
#define tomotiltsemant_h_

#include "tomotiltcommon.h"


/* macros */

#define FIELD_THETA   1
#define FIELD_ALPHA   2
#define FIELD_CORR    3
#define FIELD_SCALE   4
#define FIELD_ORIG    5
#define FIELD_PIXEL   6
#define FIELD_DEFOC   7
#define FIELD_ASTIG   8
#define FIELD_AMPCO   9
#define FIELD_REF    10

#define FIELD_AZIM   11
#define FIELD_ELEV   12
#define FIELD_OFFS   13

#define FIELD_PSI    21
#define FIELD_THE    22
#define FIELD_PHI    23

#define FIELD_PSI0   31
#define FIELD_THE0   32
#define FIELD_PHI0   33
#define FIELD_ORI0   34

#define FIELD_CS     41
#define FIELD_HT     42
#define FIELD_LAMBDA 43
#define FIELD_BETA   44
#define FIELD_FS     45

#define FIELD_PIXEL0 51


/* prototypes */

extern Size TomotiltParseToUint
            (TomotiltParse *tiltparse,
             ParseSymb *symb);

extern Index TomotiltParseToInt
             (TomotiltParse *tiltparse,
              ParseSymb *symb);

extern Coord TomotiltParseToReal
             (TomotiltParse *tiltparse,
              ParseSymb *symb);

extern void TomotiltParseStoreParam
            (TomotiltParse *tiltparse,
             int type,
             ParseSymb *err,
             Coord *val);

extern void TomotiltParseStoreAxis
            (TomotiltParse *tiltparse,
             int type,
             ParseSymb *err,
             Coord val);

extern void TomotiltParseStoreOrient
            (TomotiltParse *tiltparse,
             int type,
             ParseSymb *err,
             Coord val);

extern void TomotiltParseImage
            (TomotiltParse *tiltparse,
             ParseSymb *err,
             Size number);

extern void TomotiltParseStoreImage
            (TomotiltParse *tiltparse,
             int type,
             ParseSymb *err,
             const Coord *val,
             const Coord *val2);

extern void TomotiltParseStoreFile
            (TomotiltParse *tiltparse,
             ParseSymb *err,
             ParseSymb *sym);

extern void TomotiltParseStoreFileOffs
            (TomotiltParse *tiltparse,
             ParseSymb *err,
             Index offs);

extern void TomotiltParseEnd
            (TomotiltParse *tiltparse,
             ParseSymb *err);

extern Status TomotiltParseCommit
              (TomotiltParse *tiltparse);


#endif
