/*----------------------------------------------------------------------------*
*
*  baselib.h  -  core: various library functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef baselib_h_
#define baselib_h_

#include "defs.h"



/* prototypes */

#if OFFSETBITS == 32
#define MulOffset MulInt32
#elif OFFSETBITS == 64
#define MulOffset MulInt64
#endif

extern Size Factor
            (Size val);

extern Size FactorLE
            (Size val,
             Size maxfact);

extern Size FactorLE2
            (Size val,
             Size maxfact);

extern Size FactorGE
            (Size val,
             Size maxfact);

extern Size FactorGE2
            (Size val,
             Size maxfact);

extern Status MulSize
              (Size src1,
               Size src2,
               Size *dst);

extern Status MulInt32
              (int32_t src1,
               int32_t src2,
               int32_t *dst);

extern Status MulInt64
              (int64_t src1,
               int64_t src2,
               int64_t *dst);

extern void Swap16
            (Size size,
             const void *src,
             void *dst);

extern void Swap32
            (Size size,
             const void *src,
             void *dst);

extern void Swap64
            (Size size,
             const void *src,
             void *dst);

extern Time TimeGet();

extern Bool Select
            (const Size *selection,
             Size number);

extern Bool Exclude
            (const Size *exclusion,
             Size number);

extern Bool SelectExclude
            (const Size *selection,
             const Size *exclusion,
             Size number);


#endif
