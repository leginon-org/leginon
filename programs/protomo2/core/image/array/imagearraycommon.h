/*----------------------------------------------------------------------------*
*
*  imagearraycommon.h  -  image: array operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagearraycommon_h_
#define imagearraycommon_h_

#include "imagearray.h"


/* macros */

#define FnAsymS( srctype, dsttype, op )                                      \
  {                                                                          \
    const srctype *sp = srcpos, *se = sp + srclen;                           \
    dsttype *dp = dst;                                                       \
    while ( sp < se ) {                                                      \
      op( *sp++, dp );                                                       \
    }                                                                        \
  }                                                                          \

#define FnAsymA( srctype, dsttype, op )                                      \
  {                                                                          \
    const srctype *sp = srcpos, *se = sp + srclen;                           \
    dsttype *dp = dst;                                                       \
    while ( sp < se ) {                                                      \
      op( *sp++, dp++ );                                                     \
    }                                                                        \
  }                                                                          \

#define FnSymS( srctype, dsttype, op, symop )                                \
  {                                                                          \
    const srctype *sp = srcpos, *sn = srcneg, *se = sp + srclen, *s0 = sp;   \
    dsttype *dp = dst; Size n = dstlen;                                      \
    while ( sp < se ) {                                                      \
      op( *sp++, dp );                                                       \
    }                                                                        \
    n -= sp - s0;                                                            \
    while ( n-- ) {                                                          \
      symop( *++sn, dp );                                                    \
    }                                                                        \
  }                                                                          \

#define FnSymA( srctype, dsttype, op, symop )                                \
  {                                                                          \
    const srctype *sp = srcpos, *sn = srcneg, *se = sp + srclen;             \
    dsttype *dp = dst, *dn = dp + dstlen;                                    \
    while ( sp < se ) {                                                      \
      op( *sp++, dp++ );                                                     \
    }                                                                        \
    while ( dp < dn ) {                                                      \
      symop( *++sn, --dn );                                                  \
    }                                                                        \
  }                                                                          \


#endif
