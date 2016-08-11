/*----------------------------------------------------------------------------*
*
*  samplecommon.h  -  array: sampling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef samplecommon_h_
#define samplecommon_h_

#include "sample.h"


/* prototypes */

extern Status SampleBox
              (Size dim,
               const Size *srclen,
               const Size *smp,
               const Size *b,
               const Size *dstlen,
               const Size *c,
               Size *srcoffs,
               Size *dstoffs,
               Size *dstbox);


#endif
