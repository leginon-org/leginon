/*----------------------------------------------------------------------------*
*
*  tomoaligncommon.h  -  align: series alignment
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoaligncommon_h_
#define tomoaligncommon_h_

#include "tomoalign.h"


/* types */

typedef struct {
  const Size *sort;
  Size index;
} TomoalignInput;

typedef struct {
  Tomoalign *align;
  const char *term;
  const Size *sortprev;
  Size indexprev;
  Coord Ae[2][2];
  Coord sh[2];
  Coord pk;
} TomoalignOutput;


/* constants */

#define TomoalignInputInitializer   (TomoalignInput){ NULL, SizeMax }

#define TomoalignOutputInitializer  (TomoalignOutput){ NULL, NULL, NULL, SizeMax, TomoMat2Undef, { 0, 0 }, -CoordMax }


/* macros */

#define TomoalignLogbuflen 96


/* prototypes */

extern Status TomoalignCorrWrite
              (Tomodiagn *diagn,
               const Size index,
               const Size *srclen,
               const void *srcaddr,
               const Size *dstlen,
               Real *dstaddr,
               Real norm);

extern void TomoalignDryrunLog
            (const Tomoalign *align,
             Size index);

extern Status TomoalignSearch
              (Size thread,
               const void *inarg,
               void *outarg);

extern Status TomoalignSearchDryrun
              (Size thread,
               const void *inarg,
               void *outarg);


#endif
