/*----------------------------------------------------------------------------*
*
*  mulint64.c  -  core: multiply
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "baselib.h"
#include "exception.h"


/* functions */

extern Status MulInt64
              (int64_t src1,
               int64_t src2,
               int64_t *dst)

#define TYPE     int64_t
#define TYPEMIN  INT64_MIN
#define TYPEMAX  INT64_MAX
#define UTYPE    uint64_t
#define BITS     64

#include "mulint.h"
